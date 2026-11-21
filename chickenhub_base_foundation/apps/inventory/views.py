from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.decorators import ManagerRequiredMixin, StaffRequiredMixin
from .forms import (
    ChickenProcessingForm,
    InventoryItemForm,
    ManualStockReceiveForm,
    ProcessingOutputFormSet,
    StockAdjustmentForm,
    StockUsageForm,
    StockWastageForm,
)
from .models import ChickenProcessing, InventoryItem, ProcessingOutput, StockMovement


class InventoryDashboardView(StaffRequiredMixin, View):
    """
    Main Inventory Dashboard.
    Displays current stock levels, low-stock alerts, category filters, and quick actions.
    Accessible to all staff (Employees, Managers, Owners).
    """
    template_name = 'inventory/dashboard.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        item_type = request.GET.get('type', '').strip()
        stock_status = request.GET.get('status', '').strip()

        items = InventoryItem.objects.all().order_by('item_type', 'item_name')

        if query:
            items = items.filter(
                Q(item_name__icontains=query) | Q(item_type__icontains=query)
            )

        if item_type:
            items = items.filter(item_type=item_type)

        if stock_status == 'low':
            # Items where quantity_on_hand <= reorder_level and quantity_on_hand > 0
            items = [item for item in items if item.is_low_stock and item.quantity_on_hand > 0]
        elif stock_status == 'out':
            items = items.filter(quantity_on_hand__lte=0)
        elif stock_status == 'active':
            items = items.filter(is_active=True)

        # Calculate high-level summary metrics
        all_active_items = InventoryItem.objects.filter(is_active=True)
        low_stock_list = [i for i in all_active_items if i.is_low_stock]
        out_of_stock_count = all_active_items.filter(quantity_on_hand__lte=0).count()

        context = {
            'items': items,
            'low_stock_list': low_stock_list,
            'total_items_count': all_active_items.count(),
            'low_stock_count': len(low_stock_list),
            'out_of_stock_count': out_of_stock_count,
            'item_types': InventoryItem.ItemType.choices,
            'current_type': item_type,
            'current_status': stock_status,
            'query': query,
        }
        return render(request, self.template_name, context)


class InventoryItemCreateView(ManagerRequiredMixin, View):
    """
    Create a new Inventory Item.
    If initial stock is specified (>0), automatically logs an initial stock movement.
    """
    template_name = 'inventory/item_form.html'

    def get(self, request):
        form = InventoryItemForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Inventory Item',
            'submit_label': 'Create Item',
        })

    def post(self, request):
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item = form.save()
                # If opening balance is specified, log an initial stock movement
                if item.quantity_on_hand > 0:
                    StockMovement.objects.create(
                        inventory_item=item,
                        movement_type=StockMovement.MovementType.ADJUSTMENT,
                        quantity=item.quantity_on_hand,
                        movement_date=timezone.now(),
                        reason='Initial stock on item creation',
                        reference_number='INITIAL-STOCK',
                        recorded_by=request.user,
                    )
            messages.success(
                request,
                f"Inventory item '{item.item_name}' created successfully with {item.quantity_on_hand} {item.get_unit_of_measure_display()}."
            )
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Inventory Item',
            'submit_label': 'Create Item',
        })


class InventoryItemUpdateView(ManagerRequiredMixin, View):
    """
    Update details (name, unit, reorder level, active status) of an existing item.
    """
    template_name = 'inventory/item_form.html'

    def get(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        form = InventoryItemForm(instance=item)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Item — {item.item_name}",
            'submit_label': 'Save Changes',
            'item': item,
        })

    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        old_qty = item.quantity_on_hand
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            with transaction.atomic():
                updated_item = form.save()
                # If quantity was manually edited in the form, record an audit adjustment
                if updated_item.quantity_on_hand != old_qty:
                    diff = updated_item.quantity_on_hand - old_qty
                    StockMovement.objects.create(
                        inventory_item=updated_item,
                        movement_type=StockMovement.MovementType.ADJUSTMENT,
                        quantity=diff,
                        movement_date=timezone.now(),
                        reason=f"Direct balance edit from {old_qty} to {updated_item.quantity_on_hand}",
                        reference_number='MANUAL-EDIT',
                        recorded_by=request.user,
                    )
            messages.success(request, f"Item '{updated_item.item_name}' updated successfully.")
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Item — {item.item_name}",
            'submit_label': 'Save Changes',
            'item': item,
        })


class InventoryItemDetailView(StaffRequiredMixin, View):
    """
    Displays full details of a stock item:
    quantities, reorder level, recent movement history, and quick action shortcuts.
    """
    template_name = 'inventory/item_detail.html'

    def get(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        movements = item.stock_movements.all().order_by('-movement_date', '-created_at')[:25]
        return render(request, self.template_name, {
            'item': item,
            'movements': movements,
        })


class StockMovementListView(StaffRequiredMixin, View):
    """
    Complete audit log of all stock movements.
    Filterable by movement type, inventory item, and date.
    """
    template_name = 'inventory/movement_list.html'

    def get(self, request):
        movements = StockMovement.objects.select_related('inventory_item', 'recorded_by').all()

        movement_type = request.GET.get('type', '').strip()
        item_id = request.GET.get('item', '').strip()

        if movement_type:
            movements = movements.filter(movement_type=movement_type)

        if item_id:
            movements = movements.filter(inventory_item_id=item_id)

        items = InventoryItem.objects.all().order_by('item_name')

        context = {
            'movements': movements[:100],  # Most recent 100 entries
            'items': items,
            'movement_types': StockMovement.MovementType.choices,
            'current_type': movement_type,
            'current_item_id': item_id,
        }
        return render(request, self.template_name, context)


class RecordStockUsedView(StaffRequiredMixin, View):
    """
    Record stock used during meal preparation / cooking.
    Deducts quantity from inventory and creates a StockMovement record.
    Accessible to Employees, Managers and Owners.
    """
    template_name = 'inventory/record_usage.html'

    def get(self, request):
        initial = {}
        item_id = request.GET.get('item')
        if item_id:
            initial['inventory_item'] = item_id
        form = StockUsageForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StockUsageForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['inventory_item']
            qty = form.cleaned_data['quantity']
            movement_date = form.cleaned_data.get('movement_date') or timezone.now()
            reason = form.cleaned_data.get('reason') or 'Kitchen meal prep usage'

            with transaction.atomic():
                # Re-fetch item with select_for_update to prevent race conditions
                locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
                if qty > locked_item.quantity_on_hand:
                    messages.error(
                        request,
                        f"Cannot record usage of {qty}. Only {locked_item.quantity_on_hand} available on hand."
                    )
                    return render(request, self.template_name, {'form': form})

                locked_item.quantity_on_hand -= qty
                locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                movement = StockMovement.objects.create(
                    inventory_item=locked_item,
                    movement_type=StockMovement.MovementType.USED,
                    quantity=-qty,  # Negative change
                    movement_date=movement_date,
                    reason=reason,
                    reference_number='KITCHEN-PREP',
                    recorded_by=request.user,
                )

            messages.success(
                request,
                f"Recorded usage of {qty} {item.get_unit_of_measure_display()} of {item.item_name}. "
                f"Remaining stock: {locked_item.quantity_on_hand}."
            )
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class RecordStockWastedView(ManagerRequiredMixin, View):
    """
    Record spoiled, burned, expired, or dropped stock.
    Deducts quantity and logs audit record with required explanation.
    Restricted to Managers and Owners.
    """
    template_name = 'inventory/record_wastage.html'

    def get(self, request):
        initial = {}
        item_id = request.GET.get('item')
        if item_id:
            initial['inventory_item'] = item_id
        form = StockWastageForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StockWastageForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['inventory_item']
            qty = form.cleaned_data['quantity']
            movement_date = form.cleaned_data.get('movement_date') or timezone.now()
            reason = form.cleaned_data['reason']

            with transaction.atomic():
                locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
                if qty > locked_item.quantity_on_hand:
                    messages.error(
                        request,
                        f"Cannot record wastage of {qty}. Only {locked_item.quantity_on_hand} available on hand."
                    )
                    return render(request, self.template_name, {'form': form})

                locked_item.quantity_on_hand -= qty
                locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                StockMovement.objects.create(
                    inventory_item=locked_item,
                    movement_type=StockMovement.MovementType.WASTED,
                    quantity=-qty,
                    movement_date=movement_date,
                    reason=reason,
                    reference_number='WASTAGE-LOG',
                    recorded_by=request.user,
                )

            messages.warning(
                request,
                f"Recorded wastage of {qty} {item.get_unit_of_measure_display()} of {item.item_name}. "
                f"Remaining stock: {locked_item.quantity_on_hand}."
            )
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class RecordStockAdjustmentView(ManagerRequiredMixin, View):
    """
    Record an authorised physical stock count correction (stocktake).
    Calculates discrepancy delta and updates balance.
    Restricted to Managers and Owners.
    """
    template_name = 'inventory/record_adjustment.html'

    def get(self, request):
        initial = {}
        item_id = request.GET.get('item')
        if item_id:
            item = get_object_or_404(InventoryItem, pk=item_id)
            initial['inventory_item'] = item
            initial['new_counted_quantity'] = item.quantity_on_hand
        form = StockAdjustmentForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['inventory_item']
            new_qty = form.cleaned_data['new_counted_quantity']
            movement_date = form.cleaned_data.get('movement_date') or timezone.now()
            reason = form.cleaned_data['reason']

            with transaction.atomic():
                locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
                old_qty = locked_item.quantity_on_hand
                diff = new_qty - old_qty

                locked_item.quantity_on_hand = new_qty
                locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                StockMovement.objects.create(
                    inventory_item=locked_item,
                    movement_type=StockMovement.MovementType.ADJUSTMENT,
                    quantity=diff,
                    movement_date=movement_date,
                    reason=f"Stocktake audit: was {old_qty}, counted {new_qty}. Note: {reason}",
                    reference_number='STOCKTAKE',
                    recorded_by=request.user,
                )

            messages.success(
                request,
                f"Adjusted {item.item_name} stock from {old_qty} to {new_qty} {item.get_unit_of_measure_display()} "
                f"({'+' if diff >= 0 else ''}{diff})."
            )
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class RecordStockReceivedManualView(ManagerRequiredMixin, View):
    """
    Record manual stock received (outside standard purchase invoice).
    Increments inventory and creates a RECEIVED movement.
    """
    template_name = 'inventory/record_receive.html'

    def get(self, request):
        initial = {}
        item_id = request.GET.get('item')
        if item_id:
            initial['inventory_item'] = item_id
        form = ManualStockReceiveForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ManualStockReceiveForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['inventory_item']
            qty = form.cleaned_data['quantity']
            movement_date = form.cleaned_data.get('movement_date') or timezone.now()
            ref = form.cleaned_data.get('reference_number') or 'MANUAL-RECEIVE'
            reason = form.cleaned_data.get('reason') or 'Manual stock receipt'

            with transaction.atomic():
                locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
                locked_item.quantity_on_hand += qty
                locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                StockMovement.objects.create(
                    inventory_item=locked_item,
                    movement_type=StockMovement.MovementType.RECEIVED,
                    quantity=qty,
                    movement_date=movement_date,
                    reason=reason,
                    reference_number=ref,
                    recorded_by=request.user,
                )

            messages.success(
                request,
                f"Recorded receipt of {qty} {item.get_unit_of_measure_display()} of {item.item_name}. "
                f"New balance: {locked_item.quantity_on_hand}."
            )
            return redirect('inventory:item_detail', pk=item.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


# ===========================================================================
# Chicken Processing Views (Whole Chicken -> Portions)
# ===========================================================================

class ChickenProcessingCreateView(StaffRequiredMixin, View):
    """
    Record whole chicken processing into portions.
    1. Selects whole chicken item.
    2. Enters quantity of whole chickens processed.
    3. Records processing date.
    4. Records actual portions produced (not fixed yields; user enters exact outputs).
    5. Adds optional processing notes.
    6. Uses database transaction:
       - Checks sufficient whole chicken stock is available.
       - Deducts whole chicken stock.
       - Increases inventory for all portions produced.
       - Records stock movements for reduction (PROCESSED_OUT) and additions (PROCESSED_IN).
       - Prevents negative stock.
    """
    template_name = 'inventory/chicken_processing_form.html'

    def get(self, request):
        form = ChickenProcessingForm()
        dummy_processing = ChickenProcessing()
        formset = ProcessingOutputFormSet(instance=dummy_processing)

        whole_chicken_items = InventoryItem.objects.filter(
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            is_active=True,
        )
        portion_items = InventoryItem.objects.filter(
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            is_active=True,
        )

        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'whole_chicken_items': whole_chicken_items,
            'portion_items': portion_items,
        })

    def post(self, request):
        form = ChickenProcessingForm(request.POST)
        dummy_processing = ChickenProcessing()
        formset = ProcessingOutputFormSet(request.POST, instance=dummy_processing)

        if form.is_valid() and formset.is_valid():
            whole_item = form.cleaned_data['whole_chicken_item']
            qty_processed = form.cleaned_data['whole_chicken_quantity']
            proc_date = form.cleaned_data['processing_date']
            notes = form.cleaned_data.get('notes', '').strip()

            # Filter valid output rows
            valid_outputs = [
                f for f in formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('inventory_item')
            ]

            if not valid_outputs:
                messages.error(request, "At least one portion output must be recorded.")
                return render(request, self.template_name, {
                    'form': form,
                    'formset': formset,
                })

            with transaction.atomic():
                # 1. Lock whole chicken item and re-verify stock
                locked_whole = InventoryItem.objects.select_for_update().get(pk=whole_item.pk)
                if qty_processed > locked_whole.quantity_on_hand:
                    messages.error(
                        request,
                        f"Insufficient stock: cannot process {qty_processed} whole chickens because only "
                        f"{locked_whole.quantity_on_hand} birds are available on hand."
                    )
                    return render(request, self.template_name, {
                        'form': form,
                        'formset': formset,
                    })

                # 2. Create ChickenProcessing record
                processing = ChickenProcessing.objects.create(
                    processing_date=proc_date,
                    whole_chicken_item=locked_whole,
                    whole_chicken_quantity=qty_processed,
                    recorded_by=request.user,
                    notes=notes,
                )

                # 3. Deduct whole chickens from inventory
                locked_whole.quantity_on_hand -= qty_processed
                locked_whole.save(update_fields=['quantity_on_hand', 'updated_at'])

                # 4. Record whole chicken stock reduction movement
                StockMovement.objects.create(
                    inventory_item=locked_whole,
                    movement_type=StockMovement.MovementType.PROCESSED_OUT,
                    quantity=-qty_processed,
                    movement_date=timezone.now(),
                    reason=f"Cut {qty_processed} birds into portions (Batch #{processing.id})",
                    reference_number=f"PROC-{processing.id}",
                    recorded_by=request.user,
                )

                # 5. Process each portion output
                total_portions = Decimal('0.00')
                for out_form in valid_outputs:
                    portion_item = out_form.cleaned_data['inventory_item']
                    portion_qty = out_form.cleaned_data['quantity_produced']

                    # Save ProcessingOutput
                    ProcessingOutput.objects.create(
                        processing=processing,
                        inventory_item=portion_item,
                        quantity_produced=portion_qty,
                    )
                    total_portions += portion_qty

                    # Lock and increment portion stock
                    locked_portion = InventoryItem.objects.select_for_update().get(pk=portion_item.pk)
                    locked_portion.quantity_on_hand += portion_qty
                    locked_portion.save(update_fields=['quantity_on_hand', 'updated_at'])

                    # Record portion addition stock movement
                    StockMovement.objects.create(
                        inventory_item=locked_portion,
                        movement_type=StockMovement.MovementType.PROCESSED_IN,
                        quantity=portion_qty,
                        movement_date=timezone.now(),
                        reason=f"Produced from processing {qty_processed} whole birds (Batch #{processing.id})",
                        reference_number=f"PROC-{processing.id}",
                        recorded_by=request.user,
                    )

            messages.success(
                request,
                f"Successfully processed {qty_processed} whole chickens into {total_portions} portion cuts "
                f"(Batch #{processing.id}). Stock balances updated atomically."
            )
            return redirect('inventory:processing_detail', pk=processing.pk)

        messages.error(request, "Please correct the errors in the chicken processing form.")
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
        })


class ChickenProcessingListView(StaffRequiredMixin, View):
    """
    List of all chicken processing batches.
    Preserves processing history and audit records.
    """
    template_name = 'inventory/chicken_processing_list.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        processings = ChickenProcessing.objects.select_related(
            'whole_chicken_item', 'recorded_by'
        ).prefetch_related('outputs__inventory_item').all()

        if query:
            processings = processings.filter(
                Q(notes__icontains=query) |
                Q(whole_chicken_item__item_name__icontains=query) |
                Q(recorded_by__username__icontains=query) |
                Q(recorded_by__first_name__icontains=query)
            )

        context = {
            'processings': processings[:100],
            'query': query,
            'total_batches': ChickenProcessing.objects.count(),
        }
        return render(request, self.template_name, context)


class ChickenProcessingDetailView(StaffRequiredMixin, View):
    """
    Displays full details of a chicken processing batch:
    whole chicken input deduction, portions produced, and linked stock movement records.
    """
    template_name = 'inventory/chicken_processing_detail.html'

    def get(self, request, pk):
        processing = get_object_or_404(
            ChickenProcessing.objects.select_related('whole_chicken_item', 'recorded_by').prefetch_related('outputs__inventory_item'),
            pk=pk
        )
        movements = StockMovement.objects.filter(
            reference_number=f"PROC-{processing.id}"
        ).select_related('inventory_item')

        return render(request, self.template_name, {
            'processing': processing,
            'movements': movements,
        })

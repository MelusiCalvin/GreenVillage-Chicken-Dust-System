from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def initialize_order_history(apps, schema_editor):
    CustomerOrder = apps.get_model('orders', 'CustomerOrder')
    OrderStatusHistory = apps.get_model('orders', 'OrderStatusHistory')
    database = schema_editor.connection.alias
    OrderStatusHistory.objects.using(database).bulk_create([
        OrderStatusHistory(
            order_id=order.pk,
            previous_status='',
            new_status=order.order_status,
            reason='Status recorded when order history tracking was introduced',
            changed_at=order.order_date,
        )
        for order in CustomerOrder.objects.using(database).all().iterator()
    ])


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerorder',
            name='order_status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('PREPARING', 'Preparing'), ('READY', 'Ready'), ('COLLECTED', 'Collected'), ('CANCELLED', 'Cancelled')],
                db_index=True,
                default='PENDING',
                max_length=20,
                verbose_name='Order Status',
            ),
        ),
        migrations.AddField(
            model_name='customerorder',
            name='rejection_reason',
            field=models.TextField(blank=True, verbose_name='Rejection Reason'),
        ),
        migrations.AddField(
            model_name='customerorder',
            name='inventory_deducted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Inventory Deducted At'),
        ),
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_status', models.CharField(blank=True, max_length=20)),
                ('new_status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('PREPARING', 'Preparing'), ('READY', 'Ready'), ('COLLECTED', 'Collected'), ('CANCELLED', 'Cancelled')], max_length=20)),
                ('reason', models.TextField(blank=True)),
                ('changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='status_history', to='orders.customerorder')),
            ],
            options={
                'verbose_name': 'Order Status History',
                'verbose_name_plural': 'Order Status History',
                'ordering': ['changed_at', 'pk'],
            },
        ),
        migrations.RunPython(initialize_order_history, migrations.RunPython.noop),
    ]

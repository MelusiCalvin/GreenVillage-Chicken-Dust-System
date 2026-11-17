from django.shortcuts import render


def public_home(request):
    """
    Public landing page for ChickenHub.
    Allows customers to explore the business, view meal options,
    and learn about ordering and collection.
    Accessible publicly without authentication.
    """
    featured_meals = [
        {
            'name': 'Quarter Chicken Dust',
            'category': 'Braai Specialties',
            'description': 'Flame-braaied chicken quarter seasoned with our signature ChickenHub spice rub, served with fresh pap and relish.',
            'tag': 'Popular Choice',
            'icon': 'bi-fire',
        },
        {
            'name': 'Half Chicken Dust',
            'category': 'Braai Specialties',
            'description': 'Generous half chicken grilled over open coals to golden perfection. Paired with hearty pap and homemade gravy.',
            'tag': 'Best Value',
            'icon': 'bi-award',
        },
        {
            'name': 'Full Chicken Dust',
            'category': 'Braai Specialties',
            'description': 'A whole braaied chicken, succulent and smoky. Ideal for family sharing or gatherings, served with multiple sides.',
            'tag': 'Family Feast',
            'icon': 'bi-people',
        },
        {
            'name': 'Fresh & Frozen Whole Chickens',
            'category': 'Raw Poultry & Stock',
            'description': 'Locally sourced, clean-cut whole chickens ready for home cooking or braai.',
            'tag': 'Direct Stock',
            'icon': 'bi-box-seam',
        },
        {
            'name': 'Fresh Chicken Portions',
            'category': 'Raw Poultry & Stock',
            'description': 'Quality chicken portions (thighs, wings, drumsticks) packaged for convenience.',
            'tag': 'Fresh Cut',
            'icon': 'bi-grid',
        },
        {
            'name': 'Accompaniments & Sides',
            'category': 'Sides & Extras',
            'description': 'Traditional South African sides including hot fluffy pap, spicy chakalaka, tomato gravy and fresh salsa.',
            'tag': 'Traditional Sides',
            'icon': 'bi-cup-hot',
        },
    ]

    context = {
        'featured_meals': featured_meals,
    }
    return render(request, 'public/home.html', context)

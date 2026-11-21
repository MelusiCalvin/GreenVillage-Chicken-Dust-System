import pathlib

path = pathlib.Path('templates/dashboard/base_dashboard.html')
content = path.read_text(encoding='utf-8')

old = (
    '            <div class="sidebar-heading">Sales &amp; Orders</div>\n'
    '            <a href="#" class="sidebar-nav-link text-white-50" title="Module to be activated in next phase">\n'
    '                <i class="bi bi-receipt"></i>\n'
    '                <span>Sales &amp; POS</span>\n'
    '                <span class="badge bg-secondary ms-auto small">Soon</span>\n'
    '            </a>\n'
    '            <a href="#" class="sidebar-nav-link text-white-50" title="Module to be activated in next phase">\n'
    '                <i class="bi bi-basket3"></i>\n'
    '                <span>Customer Orders</span>\n'
    '                <span class="badge bg-secondary ms-auto small">Soon</span>\n'
    '            </a>'
)

new = (
    '            <div class="sidebar-heading">Sales &amp; Orders</div>\n'
    "            <a href=\"{% url 'sales:list' %}\" class=\"sidebar-nav-link {% if request.resolver_match.app_name == 'sales' %}active{% endif %}\">\n"
    '                <i class="bi bi-receipt"></i>\n'
    '                <span>Sales &amp; POS</span>\n'
    '            </a>\n'
    '            <a href="#" class="sidebar-nav-link text-white-50" title="Module to be activated in next phase">\n'
    '                <i class="bi bi-basket3"></i>\n'
    '                <span>Customer Orders</span>\n'
    '                <span class="badge bg-secondary ms-auto small">Soon</span>\n'
    '            </a>'
)

if old in content:
    path.write_text(content.replace(old, new), encoding='utf-8')
    print('OK - replaced')
else:
    # Try without &amp;
    old2 = old.replace('&amp;', '&')
    new2 = new.replace('&amp;', '&')
    if old2 in content:
        path.write_text(content.replace(old2, new2), encoding='utf-8')
        print('OK - replaced (bare &)')
    else:
        idx = content.find('Sales')
        print('NOT FOUND. Context:')
        print(repr(content[idx:idx+500]))

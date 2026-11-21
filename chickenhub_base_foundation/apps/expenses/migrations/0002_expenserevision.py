from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseRevision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot', models.JSONField()),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expense_revisions', to=settings.AUTH_USER_MODEL)),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='revisions', to='expenses.expense')),
            ],
            options={
                'verbose_name': 'Expense Revision',
                'verbose_name_plural': 'Expense Revisions',
                'ordering': ['-changed_at', '-pk'],
            },
        ),
    ]

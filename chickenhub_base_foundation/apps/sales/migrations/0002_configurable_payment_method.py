from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('sales', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='Payment Method'),
        ),
    ]

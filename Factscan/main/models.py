from django.db import models

class ScrappedData(models.Model):
    id = models.BigAutoField(primary_key=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    variant_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    product_url = models.TextField(blank=True, null=True)
    brand_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    sub_category = models.CharField(max_length=255, blank=True, null=True)
    diet = models.CharField(max_length=255, blank=True, null=True)
    mass_measurement_unit = models.CharField(max_length=255, blank=True, null=True)
    net_weight = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    mrp = models.CharField(max_length=255, blank=True, null=True)
    ingredients_main_ocr = models.TextField(blank=True, null=True)
    nutrients_main_ocr = models.TextField(blank=True, null=True)
    allergen_information = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)
    other_images = models.TextField(blank=True, null=True)
    front_img = models.TextField(blank=True, null=True)
    back_img = models.TextField(blank=True, null=True)
    nutrients_img = models.TextField(blank=True, null=True)
    ingredients_img = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('raw', 'raw'),
            ('combo', 'combo'),
            ('bundle', 'bundle'),
            ('importedToRaw', 'importedToRaw'),
            ('archive', 'archive'),
            ('hold', 'hold'),
            ('imageprocessed', 'imageprocessed')
        ],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scrapped_data'
        
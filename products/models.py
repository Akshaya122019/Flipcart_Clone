from django.db import models
from django.utils.text import slugify
from users.models import User


class Category(models.Model):
    name        = models.CharField(max_length=200, unique=True)
    slug        = models.SlugField(max_length=200, unique=True, blank=True)
    parent      = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='children')
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'categories'
        verbose_name_plural = 'Categories'
        ordering        = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    seller      = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='products',
                                    limit_choices_to={'role': 'seller'})
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                    null=True, related_name='products')
    name        = models.CharField(max_length=300)
    slug        = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    brand       = models.CharField(max_length=200, blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    discount    = models.PositiveIntegerField(default=0,
                                              help_text='Discount percentage 0-100')
    stock       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def discounted_price(self):
        if self.discount:
            return self.price - (self.price * self.discount / 100)
        return self.price

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name='images')
    image      = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    alt_text   = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'product_images'

    def __str__(self):
        return f'Image for {self.product.name}'


class ProductVariant(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name='variants')
    name       = models.CharField(max_length=100, help_text='e.g. Size, Color')
    value      = models.CharField(max_length=100, help_text='e.g. XL, Red')
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stock      = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_variants'

    def __str__(self):
        return f'{self.product.name} — {self.name}: {self.value}'


class Review(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name='reviews')
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='reviews')
    rating     = models.PositiveSmallIntegerField(
                    choices=[(i, i) for i in range(1, 6)])
    title      = models.CharField(max_length=200, blank=True)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('product', 'user')   # one review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.product.name} ({self.rating}★)'
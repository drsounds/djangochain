"""
Copyright (c) 2022 Alexander Forselius

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from djangochain.models import ChainedModel, Operation


@receiver(post_save, sender=ChainedModel)
def update_chained(sender, instance, created=False, **kwargs):
    action = 'UPSERT'
    if created:
        action = 'INSERT'
    else:
        action = "UPDATE"

    app_name = sender._meta.app_name

    model = f"{app_name}:{sender._meta.model_name}"

    object_id = instance.pk
    
    conditions = {
        'pk': instance.pk
    }
    

    values = {

    }

    for field in model._meta.fields:
        field_value = getattr(instance, field.name)
        if isinstance(field_value, int):
            values[field.name] = field_value
        elif isinstance(field_value, str):
            values[field.name] = field_value
        elif isinstance(field_value, float):
            values[field.name] = field_value

    operation = Operation.objects.create(
        conditions=conditions,
        action=action,
        app_name=app_name,
        object_id=object_id,
        model=model,
        values=values
    )


@receiver(post_save, sender=ChainedModel)
def delete_chained(sender, instance, origin=None):
    action = 'DELETE'

    app_name = sender._meta.app_name

    model = f"{app_name}:{sender._meta.model_name}"

    object_id = instance.pk
    
    conditions = {
        'pk': instance.pk
    } 
    
    operation = Operation.objects.create(
        conditions=conditions,
        action=action,
        app_name=app_name,
        object_id=object_id,
        model=model,
        values={}
    )

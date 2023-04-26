import logging
from datetime import timedelta

from celery import shared_task
from django.utils.translation import gettext_lazy as _

from outpost.django.campusonline import models as campusonline
from outpost.django.geo.models import Room

from .models import Organization, Person

logger = logging.getLogger(__name__)


class SynchronizationTasks:

    @shared_task(bind=True, ignore_result=True, name=f"{__name__}.Synchronization:campusonline")
    def campusonline(task):
        for cop in campusonline.Person.objects.all():
            logger.debug(f"Sync campusonline.Person {cop.pk}")
            try:
                cop.room
            except campusonline.Room.DoesNotExist:
                Person.objects.filter(campusonline_id=cop.pk).delete()
                logger.warning(f"No campusonline.Room for {cop}) ({cop.pk}), deleting Person")
                continue
            p, created = Person.objects.get_or_create(
                campusonline_id=cop.pk, defaults={"campusonline": cop}
            )
            if created:
                logger.info(f"Create {p}")
            else:
                logger.debug(f"Found {p}")
            if cop.room:
                try:
                    r = Room.objects.get(campusonline=cop.room)
                    if not p.room:
                        p.room = r
                        p.save()
                    else:
                        if p.room.pk != r.pk:
                            p.room = r
                            p.save()
                except Room.DoesNotExist:
                    logger.debug(f"No geo.Room for {cop}) ({cop.pk})")
        for p in Person.objects.all().order_by("pk"):
            logger.debug(f"Sync structure.Person {p.pk}")
            try:
                cop = campusonline.Person.objects.get(pk=p.campusonline_id)
                logger.debug(f"Found {cop}")
            except campusonline.Person.DoesNotExist:
                logger.warn(f"Remove {p.pk}")
                p.delete()
        for coo in campusonline.Organization.objects.all():
            logger.debug(f"Sync campusonline.Organization {coo} ({coo.pk})")
            o, created = Organization.objects.get_or_create(
                campusonline_id=coo.pk, defaults={"campusonline": coo}
            )
            if created:
                logger.info(f"Create {o}")
            else:
                logger.debug(f"Found {o}")
        for o in Organization.objects.all().order_by("pk"):
            logger.debug(f"Sync structure.Organization {o.pk}")
            try:
                coo = campusonline.Organization.objects.get(pk=o.campusonline_id)
                logger.debug(f"Found {coo}")
            except campusonline.Organization.DoesNotExist:
                logger.warn(f"Remove {o.pk}")
                o.delete()

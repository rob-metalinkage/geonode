from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.documents.models import Document
from geonode.layers.models import Layer


@task(name='geonode.tasks.update.geoserver_update_layers', queue='update')
def geoserver_update_layers(*args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@task(name='geonode.tasks.update.create_document_thumbnail', queue='update')
def create_document_thumbnail(object_id):
    """
    Runs the create_thumbnail logic on a document.
    """

    try:
        document = Document.objects.get(id=object_id)

    except Document.DoesNotExist:
        return

    image = document._render_thumbnail()
    filename = 'doc-%s-thumb.png' % document.id
    document.save_thumbnail(filename, image)

@task(name='geonode.tasks.update.fix_layer_thumbnail', queue='update')
def fix_layer_thumbnail(object_id):
    """
    Invokes Layer.save() in order to regenerate/fix the thumbnail
    """

    try:
        layer = Layer.objects.get(id=object_id)
    except Layer.DoesNotExist:
        return

    layer.save()

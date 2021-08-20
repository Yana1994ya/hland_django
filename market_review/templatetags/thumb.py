from django import template

from market_review import features, models, thumb_gen

register = template.Library()


@register.filter
def thumb_width(asset: features.ImageAsset, width: int):
    if width >= asset.width:
        return asset.url

    if type(asset) == models.ImageAsset:
        return asset.url

    for thumb in asset.thumbs:
        if thumb.request_width == width:
            return thumb.url

    thumb = thumb_gen.create_thumb(asset.url, asset.id, {
        "request_width": width
    }, (width, width * 20))

    # Important append to the list of thumbs to avoid duplicating if reused
    asset.thumbs.append(features.ImageAsset(
        id=thumb.id,
        key=thumb.key,
        bucket=thumb.bucket,
        width=thumb.width,
        height=thumb.height,
        request_width=thumb.request_width,
        request_height=thumb.request_height,
        thumbs=[]
    ))

    return thumb.url

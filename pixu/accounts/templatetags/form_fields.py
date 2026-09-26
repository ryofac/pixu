from django import template

register = template.Library()


@register.simple_tag
def render_accessible_field(field):
    """Render a bound field with help and validation connected to the control."""
    described_by = []
    if field.help_text:
        described_by.append(f"{field.auto_id}_help")
    if field.errors:
        described_by.append(f"{field.auto_id}_errors")

    attrs = {}
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)
    if field.errors:
        attrs["aria-invalid"] = "true"
    return field.as_widget(attrs=attrs)

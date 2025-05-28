from typing import List


class Input:
    def __init__(
            self,
            id: str,
            label: str,
            type: str,
            value: str,
            classes: List[str] = None,
            disabled: bool = False
    ):
        if classes is None:
            classes = ['form-control']
        self.id = id
        self.label = label
        self.type = type
        self.value = value
        self.classes = classes
        self.disabled = disabled

    def get_html(self):
        classes = ' '.join(self.classes)
        classes_attr = f'class="{classes}"' if len(classes) > 0 else ''
        label = f'<label for="{self.id}">{self.label}</label>'
        disabled = "disabled" if self.disabled else ""
        inpt = f'<input id="{self.id}" {classes_attr} type="{self.type}" value="{self.value}" {disabled}/>'
        return f'<div class="row">\n\t{label}\n\t{inpt}\n</div>'
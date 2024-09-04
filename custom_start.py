import os
import json
import logging
import shutil
import base64
import mimetypes

os.environ["WEBUI_SECRET_KEY"] = "..."
from open_webui.apps.webui.models.models import Models, ModelForm
from open_webui.apps.webui.models.functions import Functions, FunctionForm

# Import functions

from open_webui.config import FUNCTIONS_DIR
from open_webui.apps.webui.utils import load_function_module_by_id

with open("functions.json") as f:
    functions_specifications = json.load(f)
    for spec in functions_specifications:
        src_function_path = os.path.join("/functions", f"{spec['id']}.py")
        with open(src_function_path, "r") as f:
            spec['content'] = f.read()
        form_data = FunctionForm(**spec)
        dst_function_path = os.path.join(FUNCTIONS_DIR, f"{form_data.id}.py")
        with open(dst_function_path, "w") as f:
            f.write(form_data.content)
        function_module, function_type, frontmatter = load_function_module_by_id(
            form_data.id
        )
        if function := Functions.get_function_by_id(form_data.id):
            print(f"Updating function: {form_data.id}")
            Functions.update_function_by_id(form_data.id, form_data)
        else:
            print(f"Inserting function: {form_data.id}")
            Functions.insert_new_function("custom-start", function_type, form_data)

# Import models

with open("models.json") as f:
    models_specifications = json.load(f)
    for spec in models_specifications:
        if spec["info"]["meta"]["profile_image_url"].startswith("@"):
            filename = spec["info"]["meta"]["profile_image_url"][1:]
            mimetype, _ = mimetypes.guess_type(filename)
            data = open(filename, "rb").read()
            spec["info"]["meta"]["profile_image_url"] = f"data:{mimetype};base64,{base64.b64encode(data).decode('utf-8')}"
        form_data = ModelForm(**spec["info"])
        if model := Models.get_model_by_id(form_data.id):
            print(f"Updating model: {form_data.id}")
            Models.update_model_by_id(form_data.id, form_data)
        else:
            print(f"Inserting model: {form_data.id}")
            Models.insert_new_model(form_data, "custom-start")

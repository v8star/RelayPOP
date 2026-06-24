def merge_field(new_value, old_value, default=""):

    if new_value is None:
        return old_value or default

    if str(new_value).strip() == "":
        return old_value or default

    return new_value
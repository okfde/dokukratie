from memorious_extended.operations import clean as _clean


def clean(context, data):
    # rewrite document types
    document_types = {v: k for k, v in context.crawler.config["document_types"].items()}
    data["document_type"] = document_types[data["document_type"]]

    # make sure this data is correct:
    data["document_id"] = data["reference"].split("/")[1]

    _clean(context, data)

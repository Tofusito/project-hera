import torch  # Our Executor has dependency on torch
from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class ContainerizedEncoder(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = 'This Document is embedded by ContainerizedEncoder'
            doc.embedding = torch.randn(10)
        return docs
import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.request_limits import MetadataSafetyMiddleware
from app.visual_search import (
    DisabledVisualProvider,
    ProviderUnavailable,
    VisualQuery,
    VisualQueryKind,
)


def test_metadata_limit_and_security_headers():
    with TestClient(app) as client:
        response=client.post('/api/v1/heritage/ask',content=b'x'*(2*1024*1024+1))
        assert response.status_code==413
        assert client.get('/health').headers['x-content-type-options']=='nosniff'


def test_chunked_body_without_length_is_bounded_before_application():
    called=[]
    async def downstream(scope,receive,send):
        called.append(True)
    messages=iter([{'type':'http.request','body':b'abc','more_body':True},
                   {'type':'http.request','body':b'def','more_body':False}])
    sent=[]
    async def receive():
        return next(messages)
    async def send(message):
        sent.append(message)
    asyncio.run(MetadataSafetyMiddleware(downstream,max_bytes=5)({'type':'http','method':'POST'},receive,send))
    assert not called and sent[0]['status']==413


def test_visual_provider_is_explicitly_unavailable():
    import pytest

    with pytest.raises(ProviderUnavailable):
        DisabledVisualProvider().search(VisualQuery(source={'manuscript_id':'fixture','page_id':'p'},kind=VisualQueryKind.FRAGMENT))

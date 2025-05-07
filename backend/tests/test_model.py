import pytest
from myapp.models import MonModele

@pytest.mark.django_db
def test_model_creation():
    obj = MonModele.objects.create(nom="Test")
    assert obj.id is not None 
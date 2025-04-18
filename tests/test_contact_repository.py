import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, Mock
from datetime import date

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactsRepository
from src.schemas.contact import BaseContact, UpdateContact


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    return User(id=1, username="test_user", role="ADMIN")


@pytest.fixture
def contacts_repository(mock_session):
    return ContactsRepository(mock_session)


@pytest.fixture
def mock_contact(mock_user):
    return Contact(
        id=1,
        first_name="Mike",
        last_name="Minov",
        email="mike_minov@example.com",
        phone="1244546",
        birthday=date(1993, 2, 11),
        user=mock_user,
    )


@pytest.fixture
def mock_contacts_list(mock_user):
    return [
        Contact(
            id=1,
            first_name="Mike",
            last_name="Minov",
            email="mike_minov@example.com",
            phone="1244546",
            birthday=date(1993, 2, 11),
            user=mock_user,
        ),
        Contact(
            id=2,
            first_name="Anna",
            last_name="Smith",
            email="anna_smith@example.com",
            phone="9876543",
            birthday=date(1990, 5, 25),
            user=mock_user,
        ),
        Contact(
            id=3,
            first_name="Anna",
            last_name="Smith",
            email="anna_smith@example.com",
            phone="9876543",
            birthday=date(1990, 4, 20),
            user=mock_user,
        ),
    ]


@pytest.mark.asyncio
async def test_get_contacts(
    contacts_repository, mock_session, mock_user, mock_contacts_list
):
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_contacts(10, 0, mock_user)
    print(result)

    assert result == mock_contacts_list
    assert len(result) == 3
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contact_by_id(
    contacts_repository, mock_session, mock_user, mock_contact
):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_contact_by_id(mock_contact.id, mock_user)

    assert result == mock_contact
    assert result.id == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact(contacts_repository, mock_session, mock_user):
    contact_data = BaseContact(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone="123",
        birthday=date.today(),
    )

    mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", 3)

    result = await contacts_repository.create_contact(contact_data, mock_user)

    assert result.first_name == contact_data.first_name
    assert result.email == contact_data.email
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_remove_contact_found(
    contacts_repository, mock_session, mock_user, mock_contact
):
    contacts_repository.get_contact_by_id = AsyncMock(return_value=mock_contact)

    result = await contacts_repository.remove_contact(mock_contact.id, mock_user)
    assert result == mock_contact
    mock_session.delete.assert_called_once_with(mock_contact)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_contact_not_found(contacts_repository, mock_session, mock_user):
    contacts_repository.get_contact_by_id = AsyncMock(return_value=None)

    result = await contacts_repository.remove_contact(1, mock_user)

    assert result is None
    mock_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_update_contact(
    contacts_repository, mock_session, mock_user, mock_contact
):
    update_data = UpdateContact(first_name="Updated")
    contacts_repository.get_contact_by_id = AsyncMock(return_value=mock_contact)

    result = await contacts_repository.update_contact(
        mock_contact.id, update_data, mock_user
    )

    assert result.first_name == "Updated"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts(
    contacts_repository, mock_session, mock_user, mock_contacts_list
):
    query = ["Mike", "Minov"]
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list[0]
    mock_session.execute.return_value = mock_result

    result1 = await contacts_repository.search_contacts(query[0], user=mock_user)
    result2 = await contacts_repository.search_contacts(query[1], user=mock_user)

    assert result1 == mock_contacts_list[0]
    assert result2 == mock_contacts_list[0]
    mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contacts_repository, mock_session, mock_user, mock_contacts_list):
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list[2]
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_upcoming_birthdays(days=7, user=mock_user)

    assert result == mock_contacts_list[2]
    mock_session.execute.assert_called_once()

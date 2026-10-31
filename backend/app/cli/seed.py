from sqlalchemy.orm import Session

from app.model_registry import load_metadata
from app.modules.organizations.dependencies import get_local_org_id
from app.modules.organizations.models import Organization
from app.shared.db.session import engine


def main() -> None:
    org_id = get_local_org_id()
    load_metadata()
    with Session(engine) as session:
        with session.begin():
            if session.get(Organization, org_id) is None:
                session.add(Organization(id=org_id, name="Local workspace"))
    print("Local workspace ready.")


if __name__ == "__main__":
    main()

from fastapi.testclient import TestClient

from pt_holidays_api.app import app
from pt_holidays_api.repository import coverage, get_holidays


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_national_holidays_2026_include_easter_based_dates():
    holidays = get_holidays(2026)
    by_name = {holiday.name: holiday.date.isoformat() for holiday in holidays}
    assert by_name["Sexta-feira Santa"] == "2026-04-03"
    assert by_name["Domingo de Pascoa"] == "2026-04-05"
    assert by_name["Corpo de Deus"] == "2026-06-04"


def test_lisboa_2026_has_municipal_holiday():
    response = client.get("/holidays", params={"year": 2026, "municipality": "Lisboa"})
    assert response.status_code == 200
    data = response.json()
    municipal = [item for item in data if item["scope"] == "municipal"]
    assert municipal[0]["date"] == "2026-06-13"
    assert municipal[0]["verification_status"] == "cross_checked"


def test_madeira_regional_holidays_include_autonomy_from_2025():
    response = client.get("/holidays", params={"year": 2026, "region": "Madeira"})
    assert response.status_code == 200
    regional = {item["name"]: item["date"] for item in response.json() if item["scope"] == "regional"}
    assert regional["Dia da Autonomia"] == "2026-04-02"
    assert regional["Dia da Regiao Autonoma da Madeira e das Comunidades Madeirenses"] == "2026-07-01"
    assert regional["Primeira Oitava"] == "2026-12-26"


def test_regions_endpoint_supports_discovery():
    response = client.get("/regions")
    assert response.status_code == 200
    regions = {item["region"]: item for item in response.json()}
    assert set(regions) == {"Acores", "Madeira"}
    assert regions["Madeira"]["type"] == "autonomous_region"
    assert "Dia da Autonomia" in {holiday["name"] for holiday in regions["Madeira"]["holidays"]}


def test_municipalities_endpoint_exposes_holiday_metadata():
    response = client.get("/municipalities")
    assert response.status_code == 200
    data = response.json()
    lisboa = next(item for item in data if item["municipality"] == "Lisboa")
    assert lisboa["holiday_name"] == "Santo Antonio"
    assert lisboa["available_years"] == [2026, 2027, 2028]
    assert len(lisboa["sources"]) >= 2
    assert any(item["municipality"] == "Vila do Porto" for item in data)
    assert not any(item["municipality"] == "Vila do" for item in data)


def test_districts_endpoint_supports_discovery():
    response = client.get("/districts")
    assert response.status_code == 200
    districts = {item["district"]: item for item in response.json()}
    assert "Lisboa" in districts
    assert districts["Lisboa"]["municipality_count"] > 1
    assert "Lisboa" in districts["Lisboa"]["municipality_names"]


def test_district_alone_does_not_propagate_municipal_holidays():
    response = client.get("/holidays", params={"year": 2026, "district": "Lisboa"})
    assert response.status_code == 200
    municipal = [item for item in response.json() if item["scope"] == "municipal"]
    assert municipal == []


def test_autonomous_region_district_includes_only_regional_holidays():
    response = client.get("/holidays", params={"year": 2026, "district": "Madeira"})
    assert response.status_code == 200
    data = response.json()
    assert any(item["scope"] == "regional" for item in data)
    assert not any(item["scope"] == "municipal" for item in data)


def test_vila_real_district_does_not_inherit_murca_holiday():
    district_response = client.get("/holidays", params={"year": 2026, "district": "Vila Real"})
    assert district_response.status_code == 200
    district_dates = {
        item["date"]
        for item in district_response.json()
        if item["scope"] == "municipal"
    }
    assert "2026-05-08" not in district_dates

    municipality_response = client.get(
        "/holidays",
        params={"year": 2026, "district": "Vila Real", "municipality": "Murca"},
    )
    assert municipality_response.status_code == 200
    murca_holidays = [
        item
        for item in municipality_response.json()
        if item["scope"] == "municipal" and item["date"] == "2026-05-08"
    ]
    assert len(murca_holidays) == 1


def test_district_disambiguates_duplicate_municipality_names():
    response = client.get(
        "/holidays",
        params={"year": 2026, "district": "Faro", "municipality": "Lagoa"},
    )
    assert response.status_code == 200
    municipal = [item for item in response.json() if item["scope"] == "municipal"]
    assert len(municipal) == 1
    assert municipal[0]["district"] == "Faro"


def test_coverage_has_308_municipalities():
    assert coverage().municipalities == 308

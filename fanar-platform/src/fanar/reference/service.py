"""Reference-data service and its sources.

`ReferenceSource` is the port; two adapters implement it:
  * `LocalReferenceSource` — seed data; runs fully offline (used by tests and the spike).
  * `ManarReferenceSource` — reads through the ACL and maps Manar payloads -> Fanar models
    (the field mapping is the clean-room contract from docs/05; only shapes are mirrored).

`ReferenceService` is the façade the API and domain code depend on.
"""
from __future__ import annotations

from typing import Protocol

from fanar.domain.models import (
    AssetClass,
    Codification,
    Counterparty,
    CurveType,
    Fund,
    Instrument,
    PostingRule,
)


class ReferenceSource(Protocol):
    def funds(self) -> list[Fund]: ...
    def instruments(self) -> list[Instrument]: ...
    def posting_rules(self) -> list[PostingRule]: ...
    def counterparties(self) -> list[Counterparty]: ...
    def curve_types(self) -> list[CurveType]: ...
    def codifications(self, cls: str) -> list[Codification]: ...


class LocalReferenceSource:
    """Seed data — the STERLING fund range and a representative slice, so the stack runs offline."""

    _FUNDS = [
        Fund("3983", "STERLING BOND", "bond"),
        Fund("3984", "STERLING EQUITY", "equity"),
        Fund("3985", "STERLING SHORT TERM BOND", "bond"),
        Fund("3994", "STERLING CASH", "moneyMarket"),
        Fund("3995", "STERLING DYNAMIC", "diversified"),
        Fund("30002", "STERLING SECUR RENDEMENT", "bond"),
    ]
    _POSTING_RULES = [
        PostingRule("REPOO", "Repo obligation", AssetClass.OBL, repo_flag=True),
        PostingRule("REPOT", "Repo TCN", AssetClass.TCN, repo_flag=True),
        PostingRule("REPOOB", "Repo obligation (B)", AssetClass.OBL, repo_flag=True),
    ]
    _CURVE_TYPES = [
        CurveType("BAM", "Courbe BAM"),
        CurveType("BAM_ZC", "BAM Zéro Coupon"),
        CurveType("REPO", "Courbe REPO"),
        CurveType("PRIM", "Courbe du Primaire"),
    ]
    _CODIFS = {
        "MonetaireBaseCalcul": [
            Codification("MonetaireBaseCalcul", "R/360", "R/360", "Exact/360"),
            Codification("MonetaireBaseCalcul", "R/365", "R/365", "Exact/365"),
        ],
    }

    def funds(self) -> list[Fund]:
        return list(self._FUNDS)

    def instruments(self) -> list[Instrument]:
        return []

    def posting_rules(self) -> list[PostingRule]:
        return list(self._POSTING_RULES)

    def counterparties(self) -> list[Counterparty]:
        return [Counterparty(f.code, f.name, kind="fund") for f in self._FUNDS]

    def curve_types(self) -> list[CurveType]:
        return list(self._CURVE_TYPES)

    def codifications(self, cls: str) -> list[Codification]:
        return list(self._CODIFS.get(cls, []))


class ManarReferenceSource:
    """Reads reference data from Manar through the ACL and maps payloads -> Fanar models."""

    def __init__(self, manar: "object") -> None:  # ManarClient (typed loosely to avoid httpx import)
        self._manar = manar

    def instruments(self) -> list[Instrument]:
        rows = self._manar.query("reference.instruments", body={}) or []
        return [self._map_instrument(r) for r in rows]

    def posting_rules(self) -> list[PostingRule]:
        rows = self._manar.query("reference.posting_rules", body={}) or []
        return [self._map_poste(r) for r in rows]

    def counterparties(self) -> list[Counterparty]:
        rows = self._manar.query("reference.counterparties", body={}) or []
        return [Counterparty(r.get("code", ""), r.get("description", ""),
                             parent_entity=r.get("entitePere")) for r in rows]

    def curve_types(self) -> list[CurveType]:
        rows = self._manar.query("market.curve_types", body={}) or []
        return [CurveType(r.get("code", ""), r.get("value", ""), r.get("description", "")) for r in rows]

    def codifications(self, cls: str) -> list[Codification]:
        rows = self._manar.query("reference.codification", params={"classe": cls}) or []
        return [Codification(cls, r.get("code", ""), r.get("value", ""), r.get("description", "")) for r in rows]

    def funds(self) -> list[Fund]:  # funds come from a portfolio query in a later phase
        return []

    # ---- field mappings (docs/05) ----
    @staticmethod
    def _map_instrument(r: dict) -> Instrument:
        return Instrument(
            code=r.get("code", ""),
            isin=r.get("codeIsin"),
            category=r.get("categorie", ""),
            asset_class=_asset_class(r.get("classe")),
            issuer_id=r.get("emetteur"),
            quotation_currency=r.get("deviseCotation", "MAD"),
            settlement_currency=r.get("deviseReglement", "MAD"),
            lot_size=r.get("quotite"),
            active=str(r.get("flagActif", "O")).upper() in {"O", "OUI", "TRUE", "1"},
        )

    @staticmethod
    def _map_poste(r: dict) -> PostingRule:
        return PostingRule(
            code=r.get("code", ""),
            label=r.get("label") or r.get("description", ""),
            asset_class=_asset_class(r.get("classe")),
            sign=1 if str(r.get("posteSigne", "")).startswith("+") else (-1 if str(r.get("posteSigne", "")).startswith("-") else 1),
            repo_flag=str(r.get("flagRepo", "")).upper() in {"O", "OUI", "TRUE", "1"},
            settlement_lag_days=int(r.get("decalageLivraison") or 0),
            value_lag_days=int(r.get("decalageValeur") or 0),
            mirror_post=r.get("posteMiroir"),
            interest_post=r.get("posteInteret"),
            accrued_interest_post=r.get("posteInteretCouru"),
            collateral_post=r.get("posteCollateral"),
            provision_post=r.get("posteProvision"),
            mtm_instrument_post=r.get("posteMtmInstrument"),
        )


def _asset_class(value: str | None) -> AssetClass:
    try:
        return AssetClass((value or "OBL").upper())
    except ValueError:
        return AssetClass.OBL


class ReferenceService:
    """Façade used by the API/domain. Backed by whichever source is wired in config."""

    def __init__(self, source: ReferenceSource) -> None:
        self._source = source

    def funds(self) -> list[Fund]:
        return self._source.funds()

    def instruments(self) -> list[Instrument]:
        return self._source.instruments()

    def posting_rules(self) -> list[PostingRule]:
        return self._source.posting_rules()

    def counterparties(self) -> list[Counterparty]:
        return self._source.counterparties()

    def curve_types(self) -> list[CurveType]:
        return self._source.curve_types()

    def codifications(self, cls: str) -> list[Codification]:
        return self._source.codifications(cls)

class OpportunityNotQualified(ValueError):
    def __init__(self, reasons: tuple[str, ...]) -> None:
        self.reasons = reasons
        super().__init__(
            "opportunity is not qualified: "
            + (", ".join(reasons) if reasons else "unknown reason")
        )

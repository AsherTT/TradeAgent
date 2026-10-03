# ADR-0002: Provider-neutral ModelGateway

Status: accepted

All model calls pass through a provider-neutral gateway. Business nodes cannot instantiate provider clients. Output is accepted only after Pydantic validation. Capability checks, bounded retry, fallback, and execution metadata are gateway responsibilities.

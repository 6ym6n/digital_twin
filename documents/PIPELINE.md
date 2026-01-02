# Architecture Details

High-level data flow:

```
MATLAB/Simulink -> MQTT -> FastAPI (backend) -> WebSocket -> React (frontend)
                               |
                               +-> RAG (ChromaDB) -> LLM diagnostics
```

For the full technical write-up, see:

- [COMPREHENSIVE_DOCUMENTATION.md](COMPREHENSIVE_DOCUMENTATION.md)

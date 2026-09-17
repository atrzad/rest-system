# Catálogo de eventos de domínio

Todo evento publicado no Redis (canal `eventos:all`) segue este envelope:

```json
{
  "tipo": "pedido_criado",
  "id": "uuid-do-evento",
  "ocorrido_em": "2026-09-17T19:30:00Z",
  "mesa_numero": 12,
  "comanda_id": "uuid",
  "payload": { "...": "..." }
}
```

| Evento | Disparado por | Consumido por | Grava em `venda_evento`? |
|---|---|---|---|
| `comanda_aberta` | scan QR / abertura manual / garçom | role `salao`, dashboard | não |
| `garcom_chamado` | botão "Chamar garçom" no self-view | todos da role `salao` | não |
| `pedido_criado` | garçom lança pedido | role `cozinha`, dashboard, cliente (self-view) | sim |
| `pedido_em_preparo` | cozinha muda status | role `salao`, cliente | não |
| `pedido_pronto` | cozinha muda status | role `salao`, cliente | não |
| `pedido_entregue` | garçom confirma entrega | dashboard, cliente | não |
| `comanda_fechada` | garçom/admin fecha a conta | dashboard, role `salao` | sim |

Roteamento no `ws_manager` (fase 1, canal único + filtro na aplicação):
- Eventos de role `salao`: todas as conexões WS autenticadas com `role=salao`.
- Eventos de role `cozinha`: todas as conexões WS autenticadas com `role=cozinha`.
- Eventos de role `admin`: usados pelo dashboard (fase 6).
- Eventos de mesa específica: conexões do self-view inscritas naquela `mesa_numero` (via query param `?mesa=`).

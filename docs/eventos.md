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

Todo evento com `mesa_numero` também vai para o self-view do cliente daquela mesa.

| Evento | Disparado por | Consumido por (WebSocket) | Fato em `venda_evento` |
|---|---|---|---|
| `comanda_aberta` | cliente pelo QR/código, ou garçom | role `salao` | — |
| `garcom_chamado` | botão "Chamar garçom" no self-view | role `salao` (faixa de chamados + som) | — |
| `chamado_atendido` | garçom clica "Atender" | role `salao` (limpa a faixa em todas as telas) | — |
| `pedido_criado` | garçom lança pedido | role `cozinha` (KDS + som) | `pedido_item_criado` (1 por item) |
| `pedido_em_preparo` | cozinha | role `salao` | `pedido_status` |
| `pedido_pronto` | cozinha | role `salao` (som) | `pedido_status` |
| `pedido_entregue` | garçom | role `salao` | `pedido_status` |
| `pedido_cancelado` | cozinha (recebido/em preparo) ou garçom (recebido) | roles `cozinha` e `salao` | `pedido_status` + `pedido_item_cancelado` (estorno, valores negativos) |
| `comanda_fechada` | garçom/admin fecha a conta | roles `salao` e `admin` (dashboard atualiza na hora) | `comanda_fechada` (valor = total com taxa) |

Os fatos de `venda_evento` são gravados **na mesma transação** da operação (não dependem do Redis);
o evento no Redis é publicado depois do commit, só para o tempo real.

Roteamento (`backend/app/ws/router_bridge.py`, canal único + filtro na aplicação):
- Eventos de role: todas as conexões WS autenticadas com aquele `role` (`?token=JWT`).
- Eventos de mesa: conexões do self-view daquela mesa (`?mesa=N&t=TOKEN_DO_QR`; token errado é recusado).
- Se a conexão com o Redis cair, o listener reconecta sozinho (1s, 2s, 4s… até 30s) e registra a queda em
  `log_entry`. No navegador, ao reconectar o WebSocket a tela recarrega os dados (eventos perdidos não voltam).

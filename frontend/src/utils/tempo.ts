/** "agora", "há 3 min", "há 1 h 20 min" a partir de um ISO timestamp. */
export function tempoDesde(iso: string, agora = Date.now()): string {
  const minutos = Math.floor((agora - new Date(iso).getTime()) / 60000);
  if (minutos < 1) return "agora";
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  return `há ${horas} h${minutos % 60 ? ` ${minutos % 60} min` : ""}`;
}

// Bipe curto gerado com Web Audio (sem arquivo de som). O navegador só libera áudio depois
// de alguma interação do usuário na página, e nas telas da equipe o login já conta.
let contexto: AudioContext | null = null;

export function tocarAlerta(vezes = 2) {
  try {
    contexto ??= new AudioContext();
    const agora = contexto.currentTime;
    for (let i = 0; i < vezes; i++) {
      const oscilador = contexto.createOscillator();
      const volume = contexto.createGain();
      oscilador.frequency.value = 880;
      volume.gain.setValueAtTime(0.25, agora + i * 0.25);
      volume.gain.exponentialRampToValueAtTime(0.001, agora + i * 0.25 + 0.18);
      oscilador.connect(volume).connect(contexto.destination);
      oscilador.start(agora + i * 0.25);
      oscilador.stop(agora + i * 0.25 + 0.2);
    }
  } catch {
    // sem suporte a áudio: o alerta visual continua funcionando
  }
}

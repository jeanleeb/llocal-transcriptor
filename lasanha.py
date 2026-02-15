#!/usr/bin/env python3
"""Arte ASCII da Lasanha - a mascote do LLocal Transcriptor."""

LASANHA = r"""
            *  LLocal Transcriptor  *
     ______________________________________________
    |                                              |
    |        /\___/\      ___                      |
    |       /       \    /   \                     |
    |      | O     O |  | -_- |  zZz              |
    |      |  __w__  |   \___/                     |
    |      |/      \-'                             |
    |     /  ##  ##  \                              |
    |    |  ##    ##  |    "Transcrevo tudo         |
    |    |            |     localmente... miau!"    |
    |    | |        | |                             |
    |   _|_|________|_|_                            |
    |  | ============== |                           |
    |  |  L A S A N H A |                           |
    |  |________________|                           |
    |______________________________________________|
"""

LASANHA_DEITADA = r"""

                   ~~ Lasanha na prateleira ~~

      .----------------------------------------------------.
      |  .__          .__          .__          .__         |
      |  |  | /\___/\ |  | /\___/\|  | /\___/\ |  |       |
      |  |  |( O   O )|  |( -   - |  |( O   O )|  |       |
      |__|  | \ _w_ / |  | \ _w_ /|  | \ _w_ / |  |_______|
     /      '--\_____/-'  '--\___/-'  '--\_____/-'         /|
    /                                                     / |
   /                 /\          /\                       / .|
  |     ____________/  \___  __/  \_________            |  /
  |    /  .    .         .\\/..           . \           | /
  |   /  . .. .  LASANHA  ..  . deitadona . .\          |/
  |  /______.___olhando pra vc_._com olhao._.\         |
  | |  _     _          _     _          _     |        |
  | | | |   | |  /\_/\ | |   | | /\_/\  | |   |        |
  | | |_|   |_| ( ^.^ )|_|   |_|( ^.^ ) |_|   |        |
  | |____________\===/___________ \===/_________|        |
  |          patinha    patinha                           |
  '------------------------------------------------------'

    Pronta pra transcrever seus audios!         =^.^=
"""

LASANHA_CLOSE = r"""

              Lasanha te olhando fixamente
             enquanto transcreve seu audio

                      /\_____/\
                     /           \
                    /    __   __   \
                   |    /@@\ /@@\   |
                   |    \__/ \__/   |
                   |                |
                    \    .____.    /
                     \   '----'  /
                      \_________/
                      /  / | \  \
                     /  /  |  \  \
                   _/  /   |   \  \_
                  /__./    |    \.__\

                  {olhos azuis intensos}

                 "...miau. Ta gravando?"

"""

LASANHA_MINI = r"""
     /\_/\
    ( O.O )  ~ Lasanha diz: miau!
     > w <   Transcrevendo localmente...
    /|   |\
   (_|   |_)  =^.^=
"""

LASANHA_PRATELEIRA = r"""
    ____________________________________________________
   |     |     |     |     |     |     |     |     |    |
   |  *  |  *  |  *  |  *  |  *  |  *  |  *  |  *  |   |
   |_____|_____|_____|_____|_____|_____|_____|_____|____|
   |                                                    |
   |            /\_/\                                   |
   |     ___   ( O O )   ___                            |
   |    |   \   \ w /   /   |                           |
   |    |    '---===---'    |                            |
   |    |  ~~ corpo fofo ~~ |       LLocal              |
   |    |   branco c/       |       Transcriptor        |
   |    |    manchinhas     |       =^.^=               |
   |    |  __|_      _|__   |                           |
   |    |_/ pata    pata \_|                            |
   |________|____________|______________________________|
   |  *  |  *  |  *  |  *  |  *  |  *  |  *  |  *  |   |
   |_____|_____|_____|_____|_____|_____|_____|_____|____|

          Lasanha relaxando na caminha
         com estampa de patinhas  ~.~
"""


def mostrar_lasanha(estilo: str = "completa") -> None:
    """Mostra a arte ASCII da Lasanha no terminal."""
    artes = {
        "completa": LASANHA,
        "mini": LASANHA_MINI,
        "deitada": LASANHA_DEITADA,
        "close": LASANHA_CLOSE,
        "prateleira": LASANHA_PRATELEIRA,
    }
    print(artes.get(estilo, LASANHA))


if __name__ == "__main__":
    import sys

    estilo = sys.argv[1] if len(sys.argv) > 1 else "completa"
    if estilo == "--all":
        for nome in ["completa", "mini", "deitada", "close", "prateleira"]:
            print(f"\n{'='*56}")
            print(f"  Estilo: {nome}")
            print(f"{'='*56}")
            mostrar_lasanha(nome)
    elif estilo == "--help":
        print("Uso: python lasanha.py [completa|mini|deitada|close|prateleira|--all]")
        print()
        print("Estilos disponíveis:")
        print("  completa    - Arte principal da Lasanha (padrão)")
        print("  mini        - Versão compacta")
        print("  deitada     - Lasanha deitada na prateleira")
        print("  close       - Close nos olhos azuis da Lasanha")
        print("  prateleira  - Lasanha relaxando na caminha")
        print("  --all       - Mostra todas as artes")
    else:
        mostrar_lasanha(estilo)

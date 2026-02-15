#!/usr/bin/env python3
"""Arte ASCII da Lasanga - a mascote do LLocal Transcriptor."""

LASANGA = r"""
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
    |  |  L A S A N G A |                           |
    |  |________________|                           |
    |______________________________________________|
"""

LASANGA_DEITADA = r"""

                   ~~ Lasanga na prateleira ~~

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
  |   /  . .. .  LASANGA  ..  . deitadona . .\          |/
  |  /______.___olhando pra vc_._com olhao._.\         |
  | |  _     _          _     _          _     |        |
  | | | |   | |  /\_/\ | |   | | /\_/\  | |   |        |
  | | |_|   |_| ( ^.^ )|_|   |_|( ^.^ ) |_|   |        |
  | |____________\===/___________ \===/_________|        |
  |          patinha    patinha                           |
  '------------------------------------------------------'

    Pronta pra transcrever seus audios!         =^.^=
"""

LASANGA_CLOSE = r"""

              Lasanga te olhando fixamente
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

LASANGA_MINI = r"""
     /\_/\
    ( O.O )  ~ Lasanga diz: miau!
     > w <   Transcrevendo localmente...
    /|   |\
   (_|   |_)  =^.^=
"""

LASANGA_PRATELEIRA = r"""
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

          Lasanga relaxando na caminha
         com estampa de patinhas  ~.~
"""


def mostrar_lasanga(estilo: str = "completa") -> None:
    """Mostra a arte ASCII da Lasanga no terminal."""
    artes = {
        "completa": LASANGA,
        "mini": LASANGA_MINI,
        "deitada": LASANGA_DEITADA,
        "close": LASANGA_CLOSE,
        "prateleira": LASANGA_PRATELEIRA,
    }
    print(artes.get(estilo, LASANGA))


if __name__ == "__main__":
    import sys

    estilo = sys.argv[1] if len(sys.argv) > 1 else "completa"
    if estilo == "--all":
        for nome in ["completa", "mini", "deitada", "close", "prateleira"]:
            print(f"\n{'='*56}")
            print(f"  Estilo: {nome}")
            print(f"{'='*56}")
            mostrar_lasanga(nome)
    elif estilo == "--help":
        print("Uso: python lasanga.py [completa|mini|deitada|close|prateleira|--all]")
        print()
        print("Estilos disponíveis:")
        print("  completa    - Arte principal da Lasanga (padrão)")
        print("  mini        - Versão compacta")
        print("  deitada     - Lasanga deitada na prateleira")
        print("  close       - Close nos olhos azuis da Lasanga")
        print("  prateleira  - Lasanga relaxando na caminha")
        print("  --all       - Mostra todas as artes")
    else:
        mostrar_lasanga(estilo)

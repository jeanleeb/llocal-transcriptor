#!/usr/bin/env python3
"""Arte ASCII da Pizza - a siamesa do LLocal Transcriptor."""

PIZZA = r"""
            *  LLocal Transcriptor  *
     ______________________________________________
    |                                              |
    |         /\#####/\                            |
    |        / ####### \                           |
    |       | ## O O ## |                          |
    |       | ##  w  ## |   "Miau! Eu sou a Pizza, |
    |        \ ##=## /      a siamesa que ouve     |
    |         \_____/       tudo..."               |
    |        /       \                             |
    |       |  .   .  |                            |
    |       |         |                            |
    |       | |     | |                            |
    |      _|_|_____|_|_                           |
    |     | ============ |                         |
    |     |  P I Z Z A   |                         |
    |     |______________|                         |
    |______________________________________________|
"""

PIZZA_DEITADA = r"""

          ~~ Pizza deitada na cama ~~

  ._________________________________________________________.
  |~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^|
  |^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~|
  |~^~^~^~^~^  /\#####/\  ~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~|
  |^~^~^~^~^  /######### \  ^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~|
  |~^~^~^~^  | ### O O ###|   ~^~^~^~^~^~^~^~^~^~^~^~^~^~^|
  |^~^~^~^~  | ###  w  ## |    ^~^~^~^~^~^~^~^~^~^~^~^~^~^|
  |~^~^~^~^   \ ##===## /   ~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^|
  |^~^~^~^~^   '-------'\_________  ^~^~^~^~^~^~^~^~^~^~^~|
  |~^~^~^~^~^  /                   \  ~^~^~^~^~^~^~^~^~^~^~|
  |^~^~^~^~^  |  corpo claro  .  .  |  ^~^~^~^~^~^~^~^~^~^|
  |~^~^~^~^~  |  patinhas     .  .  |   ~^~^~^~^~^~^~^~^~^|
  |^~^~^~^~^   \  escuras    _|  |_ /    ^~^~^~^~^~^~^~^~^|
  |~^~^~^~^~^   \___________/ |  | /  ~^~^~^~^~^~^~^~^~^~^|
  |^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~|
  |_________________________________________________________|

    Pizza na cama, pronta pra ouvir seus audios!   =^.^=
"""

PIZZA_CLOSE = r"""

            Pizza te encarando com a
           cabeca tombada pro lado

                  /\#######/\
                 / ########### \
                / ############# \
               | ####  __  __#### |
               | #### /@@\/@@\### |
               | #### \__/\__/### |
               | ###             #|
                \ ##   ._____.  # /
                 \ #   '-----' # /
                  \  #########  /
                   \___________/
                       |   |
                      _|   |_
                     |___|___|

            {carinha escura, olhos azuis}

            "...precisa de legenda? miau"

"""

PIZZA_MINI = r"""
     /\##/\
    ( #O.O# )  ~ Pizza diz: miau!
     > #w# <   Ouvindo seus audios...
    /|     |\
   (_|     |_)  =^.^=
"""

PIZZA_SIAMESA = r"""
    ____________________________________________________
   |                                                    |
   |     Siamesa mode: ON                               |
   |                                                    |
   |              /\#####/\        /\___/\              |
   |             / ####### \      / . . . \             |
   |            | ## O O ## |    | .  O O. |            |
   |            | ##  w  ## |    | .  w  . |            |
   |             \ ##=## /        \ .=. /               |
   |              \_____/          \_____/              |
   |             /       \        /       \             |
   |            |  PIZZA  |      | LASANGA |            |
   |            |_________|      |_________|            |
   |                                                    |
   |         A dupla transcritora do LLocal!            |
   |                                                    |
   |    Pizza: "eu ouco"    Lasanga: "eu transcrevo"    |
   |____________________________________________________|
"""


def mostrar_pizza(estilo: str = "completa") -> None:
    """Mostra a arte ASCII da Pizza no terminal."""
    artes = {
        "completa": PIZZA,
        "mini": PIZZA_MINI,
        "deitada": PIZZA_DEITADA,
        "close": PIZZA_CLOSE,
        "dupla": PIZZA_SIAMESA,
    }
    print(artes.get(estilo, PIZZA))


if __name__ == "__main__":
    import sys

    estilo = sys.argv[1] if len(sys.argv) > 1 else "completa"
    if estilo == "--all":
        for nome in ["completa", "mini", "deitada", "close", "dupla"]:
            print(f"\n{'='*56}")
            print(f"  Estilo: {nome}")
            print(f"{'='*56}")
            mostrar_pizza(nome)
    elif estilo == "--help":
        print("Uso: python pizza.py [completa|mini|deitada|close|dupla|--all]")
        print()
        print("Estilos disponíveis:")
        print("  completa  - Arte principal da Pizza (padrão)")
        print("  mini      - Versão compacta")
        print("  deitada   - Pizza deitada na cama")
        print("  close     - Close na carinha da Pizza")
        print("  dupla     - Pizza e Lasanga juntas!")
        print("  --all     - Mostra todas as artes")
    else:
        mostrar_pizza(estilo)

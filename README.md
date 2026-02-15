# LLocal Transcriptor

Ferramenta local de transcrição e sumarização de áudio/vídeo. Roda inteiramente na sua máquina — sem envio de dados para a nuvem.

Usa [faster-whisper](https://github.com/SYSTRAN/faster-whisper) para transcrição e [Ollama](https://ollama.com/) para sumarização com LLMs locais.

## Funcionalidades

- **Transcrição em tempo real** a partir do microfone ou dispositivo de áudio do sistema
- Transcrição de arquivos de áudio e vídeo (qualquer formato suportado pelo ffmpeg)
- Detecção automática de idioma (inglês e português)
- Saída em múltiplos formatos: texto plano, SRT (legendas) e JSON
- Sumarização local via Ollama (llama3.1 por padrão)
- Detecção automática de GPU (CUDA) para transcrição acelerada
- Configuração persistente via TOML (`~/.config/llocal-transcriptor/config.toml`)

## Requisitos

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)
- [ffmpeg](https://ffmpeg.org/) instalado no sistema
- Dispositivo de áudio de entrada (microfone) para transcrição em tempo real
- (Opcional) [Ollama](https://ollama.com/) para sumarização
- (Opcional) GPU NVIDIA com CUDA para transcrição acelerada
- (Opcional) Dispositivo de áudio virtual para captura de áudio do sistema

## Instalação

```bash
git clone https://github.com/seu-usuario/llocal-transcriptor.git
cd llocal-transcriptor
uv sync
```

### Verificando a instalação

```bash
# Deve exibir a ajuda do CLI
uv run transcriptor --help

# Verifica se o ffmpeg está disponível
ffmpeg -version
```

## Uso

### Transcrição em tempo real

O modo principal do LLocal Transcriptor é a transcrição ao vivo, ideal para reuniões, aulas e entrevistas:

```bash
# Iniciar transcrição em tempo real com o microfone padrão
uv run transcriptor live

# Especificar idioma para melhor precisão
uv run transcriptor live --language pt

# Usar modelo maior para melhor qualidade
uv run transcriptor live --model medium --language pt

# Salvar a transcrição ao finalizar
uv run transcriptor live --output reuniao.txt

# Salvar em formato SRT com timestamps
uv run transcriptor live --format srt --output reuniao.srt
```

Pressione **Ctrl+C** para parar a gravação. A transcrição aparece no terminal em tempo real, com timestamps para cada segmento.

#### Capturando áudio do sistema (reuniões online)

Para transcrever reuniões do Google Meet, Zoom, Teams etc., você precisa capturar o áudio do sistema usando um dispositivo de áudio virtual:

- **Linux:** Use PulseAudio/PipeWire monitor (`pactl list sources`)
- **macOS:** Instale [BlackHole](https://existential.audio/blackhole/) ou [Soundflower](https://github.com/mattingalls/Soundflower)
- **Windows:** Use [VB-CABLE](https://vb-audio.com/Cable/)

Depois de configurar, liste os dispositivos disponíveis e use o ID do dispositivo virtual:

```bash
# Listar dispositivos de áudio
uv run transcriptor live --list-devices

# Usar um dispositivo específico (ex.: monitor do PulseAudio)
uv run transcriptor live --device 5 --language pt
```

#### Ajustando o intervalo de transcrição

O intervalo entre transcrições pode ser ajustado (padrão: 3 segundos). Intervalos menores dão resultados mais rápidos, mas intervalos maiores produzem transcrições mais precisas:

```bash
# Transcrição mais frequente (a cada 2 segundos)
uv run transcriptor live --interval 2

# Transcrição mais precisa (a cada 5 segundos)
uv run transcriptor live --interval 5
```

### Transcrição de arquivos

#### Transcrição básica

```bash
uv run transcriptor transcribe audio.mp3
```

O resultado é impresso no terminal. Para salvar em arquivo, redirecione a saída:

```bash
uv run transcriptor transcribe audio.mp3 > transcricao.txt
```

### Especificando o idioma

Por padrão, o idioma é detectado automaticamente. Para forçar um idioma específico:

```bash
# Português
uv run transcriptor transcribe audio.mp3 --language pt

# Inglês
uv run transcriptor transcribe audio.mp3 --language en
```

Forçar o idioma correto melhora a precisão e a velocidade da transcrição, especialmente com modelos menores.

### Escolhendo o modelo Whisper

```bash
# Modelo rápido para rascunhos
uv run transcriptor transcribe audio.mp3 --model tiny

# Modelo de alta qualidade (requer mais VRAM)
uv run transcriptor transcribe audio.mp3 --model large-v3
```

Veja a seção [Modelos Whisper](#modelos-whisper) para detalhes sobre cada modelo.

### Formatos de saída

```bash
# Texto plano (padrão)
uv run transcriptor transcribe audio.mp3 --format txt

# Legendas SRT (com timestamps)
uv run transcriptor transcribe audio.mp3 --format srt > legendas.srt

# JSON estruturado (com metadados e segmentos)
uv run transcriptor transcribe audio.mp3 --format json > transcricao.json
```

#### Exemplo de saída SRT

```srt
1
00:00:00,000 --> 00:00:02,500
Olá, bem-vindos à reunião.

2
00:00:02,500 --> 00:00:05,120
Vamos discutir os tópicos da semana.
```

#### Exemplo de saída JSON

```json
{
  "language": "pt",
  "language_probability": 0.97,
  "text": "Olá, bem-vindos à reunião. Vamos discutir os tópicos da semana.",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Olá, bem-vindos à reunião."
    },
    {
      "start": 2.5,
      "end": 5.12,
      "text": "Vamos discutir os tópicos da semana."
    }
  ]
}
```

### Formatos de entrada suportados

O transcriptor aceita qualquer formato de áudio ou vídeo suportado pelo ffmpeg, incluindo:

- **Áudio:** MP3, WAV, FLAC, OGG, M4A, AAC, WMA
- **Vídeo:** MP4, MKV, AVI, MOV, WebM (o áudio é extraído automaticamente)

### Combinando opções

```bash
uv run transcriptor transcribe reuniao.mp4 \
  --model medium \
  --language pt \
  --format srt > reuniao.srt
```

## Configuração

O arquivo de configuração fica em `~/.config/llocal-transcriptor/config.toml`. Ele é criado automaticamente na primeira execução ou pode ser criado manualmente. Todas as opções possuem valores padrão — você só precisa incluir o que quiser alterar.

### Exemplo completo

```toml
whisper_model = "base"
language = "auto"
ollama_model = "llama3.1"
ollama_url = "http://localhost:11434"
summary_style = "bullets"
output_format = "txt"
```

### Referência de opções

#### `whisper_model`

Modelo do Whisper usado para transcrição. Modelos maiores são mais precisos, mas mais lentos e exigem mais memória.

- **Valores:** `tiny`, `base`, `small`, `medium`, `large-v3`
- **Padrão:** `base`

#### `language`

Idioma do áudio. Usar `auto` faz a detecção automática, mas especificar o idioma correto melhora a precisão.

- **Valores:** `auto`, `en`, `pt`
- **Padrão:** `auto`

#### `ollama_model`

Modelo de LLM usado pelo Ollama para sumarização. Pode ser qualquer modelo instalado no seu Ollama.

- **Valores:** qualquer modelo disponível (`llama3.1`, `gemma2`, `mistral`, etc.)
- **Padrão:** `llama3.1`

#### `ollama_url`

URL do servidor Ollama.

- **Padrão:** `http://localhost:11434`

#### `summary_style`

Estilo de formatação do resumo gerado pelo Ollama.

- **Valores:**
  - `bullets` — lista com tópicos principais
  - `paragraph` — texto corrido resumindo o conteúdo
  - `action-items` — lista de ações e tarefas mencionadas
- **Padrão:** `bullets`

#### `output_format`

Formato padrão da saída da transcrição (pode ser sobrescrito via `--format` na linha de comando).

- **Valores:** `txt`, `srt`, `json`
- **Padrão:** `txt`

### Prioridade de configuração

As opções passadas na linha de comando sempre têm prioridade sobre o arquivo de configuração. Isso permite definir valores padrão no arquivo e sobrescrevê-los pontualmente:

```bash
# Usa whisper_model do config.toml, mas sobrescreve o formato
uv run transcriptor transcribe audio.mp3 --format json
```

## Modelos Whisper

| Modelo | Parâmetros | VRAM | Velocidade | Qualidade | Recomendação |
|---|---|---|---|---|---|
| tiny | 39M | ~1 GB | Muito rápido | Baixa | Testes rápidos e debug |
| base | 74M | ~1 GB | Rápido | Razoável | Uso geral com CPU |
| small | 244M | ~2 GB | Moderado | Boa | Bom equilíbrio custo/benefício |
| medium | 769M | ~5 GB | Lento | Muito boa | Quando a precisão importa |
| large-v3 | 1550M | ~10 GB | Muito lento | Excelente | Melhor qualidade possível |

### GPU vs CPU

O transcriptor detecta automaticamente se há uma GPU NVIDIA com CUDA disponível:

- **Com GPU (CUDA):** usa `float16` para transcrição acelerada. Modelos maiores como `medium` e `large-v3` se tornam viáveis.
- **Sem GPU (CPU):** usa `int8` (quantizado) para reduzir uso de memória. Recomenda-se usar `tiny`, `base` ou `small`.

A detecção de GPU depende do PyTorch com suporte a CUDA estar instalado. O PyTorch **não** é uma dependência obrigatória — sem ele, o transcriptor assume CPU automaticamente.

## Desenvolvimento

```bash
# Lint
uv run ruff check src/

# Formatar
uv run ruff format src/

# Type check
uv run ty check src/

# Testes
uv run pytest
```

## Licença

MIT

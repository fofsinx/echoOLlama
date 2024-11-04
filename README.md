# 🦙 `echoOLlama`: Reverse-engineered OpenAI’s [Realtime API]
> 🌟 Talk to your local LLM models in human voice and get responses in realtime!

![🦙 EchoOLlama Banner](https://github.com/user-attachments/assets/d2422917-b03a-48aa-88c8-d40f0884bd5e)

> ⚠️ **Active Development Alert!** ⚠️
>
> We're cooking up something amazing! While the core functionality is taking shape, some features are still in the oven. Perfect for experiments, but maybe hold off on that production deployment for now! 😉

## 🎯 What's `echoOLlama`?
`echoOLlama` is a cool project that lets you talk to AI models using your voice, just like you'd talk to a real person! 🗣️

Here's what makes it special:

- 🎤 You can speak naturally and the AI understands you
- 🤖 It works with local AI models (through Ollama) so your data stays private
- ⚡ Super fast responses in real-time
- 🔊 The AI talks back to you with a natural voice
- 🔄 Works just like OpenAI's API but with your own models

Think of it like having a smart assistant that runs completely on your computer. You can have natural conversations with it, ask questions, get help with tasks - all through voice! And because it uses local AI models, you don't need to worry about your conversations being stored in the cloud.

Perfect for developers who want to:
- Build voice-enabled AI applications
- Create custom AI assistants
- Experiment with local language models
- Have private AI conversations


### 🎉 What's Working Now:

![🦙 EchoOLlama Banner](https://github.com/user-attachments/assets/5ce20abf-6982-4b6b-a824-58f7d91ef7cd)

- ✅ Connection handling and session management
- ✅ Real-time event streaming
- ✅ Redis-based session storage
- ✅ Basic database interactions
- ✅ OpenAI compatibility layer
- ✅ Core WebSocket infrastructure

### 🚧 On the Roadmap:
- 📝 Message processing pipeline (In Progress)
- 🤖 Advanced response generation with client events
- 🎯 Function calling implementation with client events
- 🔊 Audio transcription service connection with client events
- 🗣️ Text-to-speech integration with client events
- 📊 Usage analytics dashboard
- 🔐 Enhanced authentication system

## 🌟 Features & Capabilities

### 🎮 Core Services
- **Real-time Chat** 💬
  - Streaming responses via websockets
  - Multi-model support via Ollama
  - Session persistence
  - 🎤 Audio Transcription (FASTER_Whisper)
  - 🗣️ Text-to-Speech (OpenedAI/Speech)

- **Coming Soon** 🔜
  - 🔧 Function Calling System
  - 📊 Advanced Analytics

### 🛠️ Technical Goodies
- ⚡ Lightning-fast response times
- 🔒 Built-in rate limiting
- 📈 Usage tracking ready
- ⚖️ Load balancing for scale
- 🎯 100% OpenAI API compatibility

## 🏗️ System Architecture
```mermaid
graph LR
    classDef userNode fill:#fff,stroke:#333,stroke-width:2
    classDef processNode fill:#87CEEB,stroke:#333,stroke-width:2,color:black
    classDef audioNode fill:#98FB98,stroke:#333,stroke-width:2,color:black
    classDef llmNode fill:#FFA07A,stroke:#333,stroke-width:2,color:black
    classDef ttsNode fill:#DDA0DD,stroke:#333,stroke-width:2,color:black
    classDef bufferNode fill:#F0E68C,stroke:#333,stroke-width:2,color:black
    classDef sessionNode fill:#E6E6FA,stroke:#333,stroke-width:2,color:black

    %% Users
    Student[("Student")]:::userNode
    Teacher[("Teacher")]:::userNode
    Elderly[("Elderly<br>Person")]:::userNode
    Professional[("Professional")]:::userNode

    %% Core Components
    WebSocket(("WebSocket<br>Layer")):::processNode
    AudioProc(("Audio<br>Processing")):::audioNode
    LLM(("LLM<br>Agent")):::llmNode
    TTS(("TTS<br>Engine")):::ttsNode
    Buffer(("Buffer<br>Manager")):::bufferNode
    Session(("Session<br>Controller")):::sessionNode

    %% Connections
    Student --> |"Voice Input"| WebSocket
    Teacher --> |"Voice Input"| WebSocket
    Elderly --> |"Voice Input"| WebSocket
    Professional --> |"Voice Input"| WebSocket

    WebSocket --> |"Audio Buffer"| Buffer
    Buffer --> |"Processed Audio"| AudioProc
    AudioProc --> |"VAD Detection"| AudioProc
    AudioProc --> |"Transcription"| LLM
    LLM --> |"Response"| TTS
    TTS --> |"Audio Stream"| WebSocket
    WebSocket --> |"Voice Output"| Student
    WebSocket --> |"Voice Output"| Teacher
    WebSocket --> |"Voice Output"| Elderly
    WebSocket --> |"Voice Output"| Professional

    %% Component Groups
    subgraph "Real-time Processing Layer"
        WebSocket
        Buffer
        AudioProc
    end

    subgraph "AI Processing Layer"
        LLM
        TTS
    end

    %% System Notes
    note1["Each connection starts<br>a new session"]
    note2["VAD controls when<br>to respond"]
    note3["Background jobs handle<br>transcription"]
    note4["Streaming responses<br>reduce latency"]
    note5["Audio buffers processed<br>in chunks of 20ms"]
    note6["Context maintained<br>across conversations"]
    note7["Adaptive response<br>timing system"]
    note8["Multi-modal context<br>awareness"]
    note9["Dynamic buffer<br>management"]
    note10["Session state<br>persistence"]

    %% Technical Annotations
    noteWebSocket["WebSocket maintains<br>persistent connections"]
    noteBuffer["Circular buffer with<br>adjustable size"]
    noteAudio["Real-time VAD with<br>configurable threshold"]
    noteLLM["Streaming tokens with<br>context window"]
    noteTTS["Voice cloning &<br>style transfer"]

    %% User Personas
    noteStudent["Quick learner seeking<br>immediate responses<br>Prefers dynamic pace"]
    noteTeacher["Needs precise and<br>detailed interactions<br>Values accuracy"]
    noteElderly["Prefers slower, clearer<br>voice responses<br>Needs patience"]
    noteProfessional["Requires technical<br>depth and context<br>Time-sensitive"]

    %% Connecting Notes
    note1 -.-> WebSocket
    note2 -.-> AudioProc
    note3 -.-> AudioProc
    note4 -.-> TTS
    note5 -.-> Buffer
    note6 -.-> LLM
    note7 -.-> AudioProc
    note8 -.-> LLM
    note9 -.-> Buffer
    note10 -.-> Session

    noteWebSocket -.-> WebSocket
    noteBuffer -.-> Buffer
    noteAudio -.-> AudioProc
    noteLLM -.-> LLM
    noteTTS -.-> TTS

    noteStudent -.-> Student
    noteTeacher -.-> Teacher
    noteElderly -.-> Elderly
    noteProfessional -.-> Professional

    %% System States
    state1["Initialization"]
    state2["Processing"]
    state3["Response"]
    state4["Idle"]

    state1 -.-> WebSocket
    state2 -.-> AudioProc
    state3 -.-> TTS
    state4 -.-> Buffer
```

## 💻 Tech Stack Spotlight
### 🎯 Backend Champions
- 🚀 FastAPI - Lightning-fast API framework
- 📝 Redis - Blazing-fast caching & session management
- 🐘 PostgreSQL - Rock-solid data storage

### 🤖 AI Powerhouse
- 🦙 Ollama - Local LLM inference
- 🎤 faster_whisper - Speech recognition (coming soon)
- 🗣️ OpenedAI TTS - Voice synthesis (coming soon)

## 🚀 Get Started in 3, 2, 1...

1. **Clone & Setup** 📦
```bash
git clone https://github.com/iamharshdev/EchoOLlama.git
cd EchoOLlama
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Environment Setup** ⚙️
```bash
cp .env.example .env
# Update .env with your config - check .env.example for all options!
make migrate # create db and apply migrations
```

3. **Launch Time** 🚀
```bash
# Fire up the services
docker-compose up -d

# Start the API server
uvicorn app.main:app --reload
```

## 🤝 Join the EchoOLlama Family
Got ideas? Found a bug? Want to contribute? Check out our [CONTRIBUTING.md](CONTRIBUTING.md) guide and become part of something awesome! We love pull requests! 🎉

## 💡 Project Status Updates
- 🟢 **Working**: Connection handling, session management, event streaming
- 🟡 **In Progress**: Message processing, response generation
- 🔴 **Planned**: Audio services, function calling, analytics

## 📜 License
MIT Licensed - Go wild! See [LICENSE](LICENSE) for the legal stuff.

---
*Built with 💖 by the community, for the community*

*PS: Star ⭐ us on GitHub if you like what we're building!*

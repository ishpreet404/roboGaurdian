# Raspberry Pi Chatbot

This project implements a chatbot that utilizes a Raspberry Pi Bluetooth speaker for audio output and interacts with a GitHub model API for generating responses.

## Features

- **Bluetooth Audio Output**: Connects to a Raspberry Pi Bluetooth speaker to play audio responses.
- **Chatbot Functionality**: Manages conversation flow and context using a conversation manager.
- **GitHub Model Integration**: Interacts with a GitHub model API to generate responses based on user input.
- **State Management**: Maintains conversation state for a seamless user experience.

## Project Structure

```
raspi-chatbot
├── src
│   ├── __init__.py
│   ├── main.py                # Entry point for the chatbot application
│   ├── chatbot
│   │   ├── __init__.py
│   │   ├── convo_manager.py    # Manages conversation state and flow
│   │   └── state_store.py      # Handles storage and retrieval of conversation states
│   ├── audio
│   │   ├── __init__.py
│   │   └── bluetooth_speaker.py # Manages Bluetooth speaker connection and audio playback
│   └── services
│       ├── __init__.py
│       └── github_model_client.py # Interacts with the GitHub model API
├── config
│   └── settings.example.env     # Example environment configuration file
├── tests
│   ├── __init__.py
│   └── test_chatbot.py          # Unit tests for chatbot functionality
├── requirements.txt              # Project dependencies
├── pyproject.toml                # Project configuration
└── README.md                     # Project documentation
```

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/raspi-chatbot.git
   cd raspi-chatbot
   ```

2. **Install Dependencies**:
   Ensure you have Python 3 installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file and update it with your API keys:
   ```bash
   cp config/settings.example.env .env
   ```

4. **Run the Chatbot**:
   Start the chatbot application:
   ```bash
   python src/main.py
   ```

   ### Automated Raspberry Pi Setup

   On a Raspberry Pi you can automate the provisioning steps with the included
   script. Ensure the `GITHUB_TOKEN` environment variable is exported beforehand
   and that your Bluetooth speaker is already paired.

   ```bash
   chmod +x setup_pi_chatbot.sh
   GITHUB_TOKEN="ghp_your_new_token" ./setup_pi_chatbot.sh --speaker "AA:BB:CC:DD:EE:FF"
   ```

   The script installs required system packages (bluez, espeak-ng, etc.), creates
   the Python virtual environment, installs dependencies, and writes a `.env` file
   with the correct GitHub Models configuration (`openai/gpt-5-chat`). After it
   completes you can activate the virtual environment and run:

   ```bash
   source venv/bin/activate
   python src/pi_voice_chatbot.py
   ```

## Usage

Interact with the chatbot through the console. The chatbot will respond using the Raspberry Pi Bluetooth speaker.  The new
entry point `src/pi_voice_chatbot.py` powers both `src/main.py` and any
custom automation scripts; it will:

- Connect to your paired Bluetooth speaker (using the MAC address or name
   defined in `BLUETOOTH_DEVICE_IDENTIFIER`).
- Maintain conversation context locally so the assistant remembers the last
   few exchanges.
- Call the GitHub Models API (via `https://models.github.ai/inference`) using
   the personal access token stored in `GITHUB_TOKEN`.
- Read responses aloud via the system's default audio output.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
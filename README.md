# Leitner System Telegram Bot

This is a Telegram bot that helps you to learn and memorize information using the Leitner system, a popular method of spaced repetition. The bot allows users to add, review, edit, and delete flashcards, and provides daily reminders for reviewing flashcards.

## Features

- **Add Flashcards**: Simply send the text to the bot, and it will be added as a flashcard.
- **Review Flashcards**: Use the `/review` command to review flashcards that are due for today.
- **Edit and Delete Flashcards**: Use the `/edit` command to edit or delete flashcards.
- **Daily Reminders**: Toggle daily reminders using the `/reminder` command.
- **Flashcard Box Status**: Use the `/box` command to view the status of your flashcard boxes.
- **Help**: Use the `/help` command to get information about how the bot works and the Leitner system.
- **Commands List**: Use the `/commands` command to see a list of available commands.

## Commands

- `/start` - Register yourself and start using the bot.
- `/commands` - List all available commands.
- `/review` - Review flashcards due for today.
- `/reminder` - Toggle daily reminders.
- `/box` - Display the status of your flashcard boxes.
- `/all` - Display all your flashcards.
- `/edit` - Edit or delete flashcards.
- `/help` - Show help message about how the bot works and what is the Leitner system.
- `/new` - Show how to add new flashcards.
- `/bulk` - Import flashcards in bulk from a CSV formatted text, a table, a CSV file, or an Excel file.

## How It Works

1. **Add Flashcards**: Just send a message to the bot with the text you want to add as a flashcard.
2. **Review Flashcards**: The bot will show you the flashcards due for review. You can mark them as "True" or "False" based on whether you remembered the content or not.
3. **Leitner System**: Flashcards are placed in different boxes. If you remember a flashcard correctly, it moves to the next box, increasing the interval before you review it again. If you answer incorrectly, the flashcard moves back to the first box, ensuring you review it more frequently.
4. **Daily Reminders**: The bot can send daily reminders to review your flashcards. Use the `/reminder` command to enable or disable this feature.

## Setup and Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/mhe931/leitner-telegram-bot.git
   cd leitner-telegram-bot
   ```
2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```
4. Set up your configuration:

* Create a file named `.env` in the project directory.
* Add the following content to the `.env` file:

```
TELEGRAM_BOT_TOKEN='your-telegram-bot-token'
ADMIN_ID='your-admin-telegram-id'
```

5. Run the bot:

```bash
python main.py
```

## Deployment on a Digital Ocean Droplet

1.  **Create a Droplet**: Create a new Droplet on Digital Ocean. A basic Droplet with Ubuntu should be sufficient.

2.  **Connect to your Droplet**: Connect to your Droplet using SSH.

3.  **Install Dependencies**: Install the necessary dependencies on your Droplet:

    ```bash
    sudo apt-get update
    sudo apt-get install python3-venv python3-pip git
    ```

4.  **Clone the Repository**: Clone your repository to the Droplet:

    ```bash
    git clone https://github.com/your-username/leitner-telegram-bot.git
    cd leitner-telegram-bot
    ```

5.  **Set up the Environment**: Create a virtual environment and install the dependencies:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

6.  **Create the `.env` file**: Create a `.env` file with your Telegram bot token and admin ID:

    ```bash
    nano .env
    ```

    Add the following content to the file:

    ```
    TELEGRAM_BOT_TOKEN=your-telegram-bot-token
    ADMIN_ID=your-admin-telegram-id
    ```

7.  **Create the `systemd` Service File**: Create a `systemd` service file to run the bot as a service:

    ```bash
    sudo nano /etc/systemd/system/leitner-bot.service
    ```

    Add the following content to the file, replacing `your_user`, `your_group`, and `/path/to/your/project` with your actual user, group, and project path:

    ```
    [Unit]
    Description=Leitner Telegram Bot
    After=network.target

    [Service]
    User=your_user
    Group=your_group
    WorkingDirectory=/path/to/your/project
    ExecStart=/path/to/your/project/venv/bin/python main.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

8.  **Start and Enable the Service**: Start the service and enable it to start on boot:

    ```bash
    sudo systemctl start leitner-bot
    sudo systemctl enable leitner-bot
    ```

9.  **Check the Status**: You can check the status of the service with the following command:

    ```bash
    sudo systemctl status leitner-bot
    ```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License.

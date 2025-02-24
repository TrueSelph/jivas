import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from action { Action }

node STTAction :Action: {
    # The Speech-to-text base action for all STT actions.

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has api_key:str = "";
    has model:str = "";

    can invoke(audio_url:str) {
        # """
        # Convert speech to text and return text.

        # :param audio_url:
        # :return: text transcript of audio
        # """

        # override with specifics of STT model then save in audio
    }

    can invoke_base64(audio_base64:str, audio_type:str="audio/mp3") {
        # """
        # Convert an audio file from a base64 string to text using Deepgram API.

        # :param audio_base64: Base64 representation of the audio file
        # :param audio_type: mimetype of the audio file
        # :return: Transcription text
        # """

        # override with specifics of STT model then save in audio
    }

}

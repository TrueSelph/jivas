import:py os;
import:py uuid;
import:py base64;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from action { Action }
import:py from jvserve.lib.file_interface { file_interface }

node TTSAction :Action: {
    # The Text-to-speech base action for all TTS actions.

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has api_key:str = "";
    has model:str = "";

    can invoke(text:str, as_base64:bool=False, as_url:bool=False) {
        # """
        # Convert text to speech and save the audio file.

        # :param text: Text to convert to speech
        # :param as_base64: outputs audio file as base64 encoded string
        # :param as_url: outputs URL for downloading audio file
        # :return: Path to the saved audio file or base64 encoded string
        # """

        # override with specifics of TTS model then save in audio
        audio = None;

        # self.get_audio_file must be called in return statement
        return self.get_audio_as(audio, as_base64, as_url);
    }

    can get_audio_as(audio:bytes, as_base64:bool=False, as_url:bool=False) {
        # prepares the audio bytes as base64 string or url for download

        if not audio {
            return None;
        }

        try {

            if(as_base64) {
                # return a base 64 encoded representation of the audio file
                return base64.b64encode(audio).decode('utf-8');
            }

            # Save the audio content to a file
            output_file_name = f"{str(uuid.uuid4())}.mp3";
            output_file_path = f"{os.environ.get('JIVAS_FILES_ROOT_PATH','.files')}/tts/{output_file_name}";

            # output the file
            file_interface.save_file("tts/" + output_file_name, audio);

            if(as_url) {
                # return f"{os.environ.get('JIVAS_FILES_URL','http://localhost:9000/files')}/tts/{output_file_name}";
                return file_interface.get_file_url("tts/" + output_file_name);
            }

            return os.path.abspath(output_file_path);

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }
}

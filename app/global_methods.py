
import re

def wrap_words_with_span(text):
    # Regular expression to match words of 2 or more characters
    words = re.findall(r'\S+', text)  # \S+ matches any sequence of non-whitespace characters

    wrapped_text = ''
    
    for word in words:
        # Use regular expression to remove punctuation from word
        cleaned_word = re.sub(r'[^\w\s]', '', word)

        if len(cleaned_word) > 1:  # Only wrap words that have more than 1 letter
            wrapped_text += f"<span>{word}</span> "
        else:
            wrapped_text += word + ' '

    return wrapped_text.strip()

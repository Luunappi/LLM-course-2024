#!/bin/bash

# Tarkista onko OPENAI_API_KEY asetettu
if [ -z "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY ei ole asetettu!"
    echo "Aseta se komennolla: export OPENAI_API_KEY=your-key-here"
    exit 1
fi

# Käynnistä Streamlit sovellus
streamlit run src/main.py 
FROM fmantuano/spamscope-deps

# environment variables
ARG SPAMSCOPE_VER="develop"

ENV SPAMASSASSIN_ENABLED="True" \
    SPAMSCOPE_CONF_FILE="/etc/spamscope/spamscope.yml" \
    SPAMSCOPE_PATH="/opt/spamscope" \
    THUG_ENABLED="True"

# install SpamScope
RUN set -ex; \
    mkdir -p "/var/log/spamscope" "/etc/spamscope"; \
    git clone -b ${SPAMSCOPE_VER} --single-branch https://github.com/SpamScope/spamscope.git ${SPAMSCOPE_PATH}; \
    cd $SPAMSCOPE_PATH; \
    pip install -r requirements_optional.txt; \
    python setup.py install; \
    sparse jar -s; \
    pip install -U thug;
    
WORKDIR ${SPAMSCOPE_PATH}

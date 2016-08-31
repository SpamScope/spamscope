(ns spamscope
  (:use     [streamparse.specs])
  (:gen-class))

(defn spamscope [options]
   [
    ;; spout configuration
    {"files-mails-spout" (python-spout-spec
          options
          "spouts.files_mails.FilesMailSpout"
          ["mail_path", "mail_server", "mailbox", "priority", "kind_data"]
          :p 1 ;; MUST be 1 for this spout          
          :conf {
                 "spouts.conf", "/etc/spamscope/spouts.yml",
                 }
          )
    }
    ;; bolt configuration
    {"tokenizer-bolt" (python-bolt-spec
          options
          {"files-mails-spout" :shuffle}
          "bolts.tokenizer.Tokenizer"
          ["sha256_random", "mail"]
          :p 2
          )
    "attachments-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["sha256_random"]}
          "bolts.attachments.Attachments"
          ["sha256_random", "with_attachments", "attachments_json"]
          :p 2
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "urls_handler_body-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["sha256_random"]}
          "bolts.urls_handler_body.UrlsHandlerBody"
          ["sha256_random", "with_urls_body", "urls"]
          :p 1
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "urls_handler_attachments-bolt" (python-bolt-spec
          options
          {"attachments-bolt" ["sha256_random"]}
          "bolts.urls_handler_attachments.UrlsHandlerAttachments"
          ["sha256_random", "with_urls_attachments", "urls"]
          :p 1
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "phishing-bolt" (python-bolt-spec
          options
          {
           "tokenizer-bolt" ["sha256_random"]
           "attachments-bolt" ["sha256_random"]
           "urls_handler_body-bolt" ["sha256_random"]
           "urls_handler_attachments-bolt" ["sha256_random"]
           }
          "bolts.phishing.Phishing"
          ["sha256_random", "with_phishing", "score", "targets"]
          :p 2
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "forms-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["sha256_random"]}
          "bolts.forms.Forms"
          ["sha256_random", "forms"]
          :p 1
          )
    "json-bolt" (python-bolt-spec
          options
          {
           "tokenizer-bolt" ["sha256_random"]
           "phishing-bolt" ["sha256_random"]
           "attachments-bolt" ["sha256_random"]
           "forms-bolt" ["sha256_random"]
           "urls_handler_body-bolt" ["sha256_random"]
           "urls_handler_attachments-bolt" ["sha256_random"]
           }
          "bolts.json_maker.JsonMaker"
          ["sha256_random", "mail"]
          :p 2
          )
    "output-debug-bolt" (python-bolt-spec
          options
          {"json-bolt" :shuffle}
          "bolts.output_debug.OutputDebug"
          []
          :p 1
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "output-redis-bolt" (python-bolt-spec
          options
          {"json-bolt" :shuffle}
          "bolts.output_redis.OutputRedis"
          []
          :p 1
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    "output-elasticsearch-bolt" (python-bolt-spec
          options
          {"json-bolt" :shuffle}
          "bolts.output_elasticsearch.OutputElasticsearch"
          []
          :p 1
          :conf {
                 "bolts.conf", "/etc/spamscope/bolts.yml",
                 }
          )
    }
  ]
)

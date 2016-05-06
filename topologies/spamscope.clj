(ns spamscope
  (:use     [streamparse.specs])
  (:gen-class))

(defn spamscope [options]
   [
    ;; spout configuration
    {"mails-spout" (python-spout-spec
          options
          "spouts.mails.MailSpout"
          ["mail_path"]
          :p 1           
          )
    }
    ;; bolt configuration
    {"tokenizer-bolt" (python-bolt-spec
          options
          {"mails-spout" :shuffle}
          "bolts.tokenizer.Tokenizer"
          ["sha256_random", "mail"]
          :p 1
          )
    "phishing-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["sha256_random"]}
          "bolts.phishing.Phishing"
          ["sha256_random", "phishing"]
          :p 1
          )
    "attachments-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["sha256_random"]}
          "bolts.attachments.Attachments"
          ["sha256_random", "with_attachments", "attachments_json"]
          :p 1
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
           }
          "bolts.json_maker.JsonMaker"
          ["sha256_random", "mail"]
          :p 1
          )
    "output-debug-bolt" (python-bolt-spec
          options
          {"json-bolt" :shuffle}
          "bolts.output_debug.OutputDebug"
          []
          :p 2
          )
    }
  ]
)

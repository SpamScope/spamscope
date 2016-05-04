(ns spamscope
  (:use     [streamparse.specs])
  (:gen-class))

(defn spamscope [options]
   [
    ;; spout configuration
    {"mails-spout" (python-spout-spec
          options
          "spouts.mails.MailSpout"
          ["message_id"]
          :p 1           
          )
    }
    ;; bolt configuration
    {"tokenizer-bolt" (python-bolt-spec
          options
          {"mails-spout" :shuffle}
          "bolts.tokenizer.Tokenizer"
          ["message_id", "mail"]
          :p 1
          )
    "phishing-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["message_id"]}
          "bolts.phishing.Phishing"
          ["message_id", "phishing"]
          :p 1
          )
    "attachments-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["message_id"]}
          "bolts.attachments.Attachments"
          ["message_id", "with_attachments", "attachments_json"]
          :p 1
          )
    "forms-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["message_id"]}
          "bolts.forms.Forms"
          ["message_id", "forms"]
          :p 1
          )
    "json-bolt" (python-bolt-spec
          options
          {
           "tokenizer-bolt" ["message_id"]
           "phishing-bolt" ["message_id"]
           "attachments-bolt" ["message_id"]
           "forms-bolt" ["message_id"]
           }
          "bolts.json_maker.JsonMaker"
          []
          :p 1
          )
    }
  ]
)

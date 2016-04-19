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
          ["mail_path", "mail"]
          :p 1
          )
    "phishing-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["mail_path"]}
          "bolts.phishing.Phishing"
          ["mail_path"]
          :p 1
          )
    "attachments-bolt" (python-bolt-spec
          options
          {"tokenizer-bolt" ["mail_path"]}
          "bolts.attachments.Attachments"
          ["mail_path", "with_attachment", "attachments_json"]
          :p 1
          )
    }
  ]
)

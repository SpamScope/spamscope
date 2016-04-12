(ns spamscope
  (:use     [streamparse.specs])
  (:gen-class))

(defn spamscope [options]
   [
    ;; spout configuration
    {"mails-spout" (python-spout-spec
          options
          "spouts.mails.MailSpout"
          ["mail"]
          )
    }
    ;; bolt configuration
    {"mailparse-bolt" (python-bolt-spec
          options
          {"mails-spout" :shuffle}
          "bolts.mailparse.MailParser"
          []
          )
    }
  ]
)

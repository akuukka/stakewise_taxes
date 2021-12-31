(require 'cl-lib)

(defun compute-income (interest capital compound-interval compound-gas-fee)
  "Computes stakewise total annual income"
  (let ((rewards 0.0) (day 0) (compound-counter 0) (days-until-compound compound-interval))
    (while (< day 365)
      (setq rewards (+ rewards (* capital (/ interest 365.0))  ))
      (setq days-until-compound (- days-until-compound 1))
      (when (= days-until-compound 0)
        (setq capital (+ capital (- rewards compound-gas-fee)))
        (setq rewards 0)
        (cl-incf compound-counter)
        (setq days-until-compound compound-interval))
      (cl-incf day))
    (setq total (+ capital rewards))
    total))

(defun compute-optimal-compound-interval (capital interest compound-gas-fee)
  "Computes optimal compound interval (days)."
  (let ((compound-interval 365) (best-total -1.0) (best-interval -1))
    (while (> compound-interval 0)
      (let ((total (compute-income interest capital compound-interval compound-gas-fee)))
        (when (> total best-total)
          (setq best-total total)
          (setq best-interval compound-interval)))
      (cl-decf compound-interval))
    (list best-interval best-total)))

;; Example:
;; 1000 ETH
;; 5% APR
;; Compound operation costs 0.01 ETH
;; => optimal compound interval is 34 days (with that, you have 1051.049 ETH after 365 days)
(compute-optimal-compound-interval 1000 0.05 0.01)

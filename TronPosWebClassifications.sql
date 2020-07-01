CREATE TABLE TronPosWebClassifications (
    id INT NOT NULL,
    tpfirm_id INT FOREIGN KEY REFERENCES TronPosOdooExchangeUp(tpfirm_id),
    TopWebClassificationGUID NVARCHAR(255) NOT NULL,
    Name NVARCHAR(50) NULL,
    PRIMARY KEY(id)
)
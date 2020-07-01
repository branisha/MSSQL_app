CREATE TABLE TronPosOdooExchangeUp (
    tpfirm_id INT NOT NULL,
    tpfirmName NVARCHAR(255) NOT NULL,
    tpfirmActive BIT NOT NULL,
    TronRetailServerDataBase NVARCHAR(255) NOT NULL,
    OdooHost NVARCHAR(255) NOT NULL,
    OdooPort INT NOT NULL,
    OdooDataBase NVARCHAR(255) NOT NULL,
    OdooUserName NVARCHAR(255) NOT NULL,
    OdooPassword NVARCHAR(255) NOT NULL,
    recDate DATETIME NULL,
    OdooECommerce BIT NULL,
    RowChID BIGINT NOT NULL,
    SyncClientUser NVARCHAR(255) NULL,
    SyncClientPassword NVARCHAR(1000) NULL,
    WebClassificationTable NVARCHAR(50) NULL,
    TopWebClassifications NVARCHAR(50) NULL,
    PRIMARY KEY(tpfirm_id)
)
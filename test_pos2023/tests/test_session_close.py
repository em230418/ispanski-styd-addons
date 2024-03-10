import inspect
import logging

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestSessionClose(TestPoSCommon):
    def setUp(self):
        super(TestPoSCommon, self).setUp()
        self.product1 = self.env["product.product"].create(
            {
                "type": "consu",
                "available_in_pos": True,
                "taxes_id": [(5, 0, 0)],
                "name": "Consumable Product 1",
                "categ_id": self.categ_basic.id,
                "lst_price": 10.0,
                "standard_price": 5,
            }
        )

    def test_late_session_close(self):
        method_name = inspect.currentframe().f_code.co_name
        config1 = self._create_basic_config()
        config2 = self._create_basic_config()

        # В первом POS открываем сессию
        self.config = config1
        self.open_new_session()
        session1 = self.pos_session

        # Оплачиваем наличкой один заказ
        orders = []
        orders.append(
            self.create_ui_order_data(
                [(self.product1, 1)], payments=[(self.cash_pm, 10)],
            )
        )

        self.env["pos.order"].create_from_ui(orders)

        # Не закрываем сессию в первом POS
        # и открываем и закрываем много сессий на втором POS-е
        # в каждой сессии также по одному заказу оплачиваем наличкой
        self.config = config2

        for i in range(1000):
            _logger.info("%s: running session %s" % (method_name, i))
            self.open_new_session()
            order = self.create_ui_order_data(
                [(self.product1, 1)], payments=[(self.cash_pm, 10)],
            )
            self.env["pos.order"].create_from_ui([order])
            self.pos_session.action_pos_session_validate()

        # Ну а теперь попробуем закрывать самую первую сессию
        _logger.info("closing very first session")
        session1.action_pos_session_validate()

    def test_1000_pos_configs(self):
        method_name = inspect.currentframe().f_code.co_name
        configs = [self._create_basic_config() for x in range(1000)]

        for i, pos in enumerate(configs):
            # открываем очередную кассу
            _logger.info("%s: running session %s" % (method_name, i))
            self.config = pos
            self.open_new_session()

            # заказываем что-то
            orders = []
            orders.append(
                self.create_ui_order_data(
                    [(self.product1, 1)], payments=[(self.cash_pm, 10)],
                )
            )
            self.env["pos.order"].create_from_ui(orders)

            if i == 0:
                # первую сессию просто запоминаем
                first_session = self.pos_session
            else:
                # остальные сессии закрываем
                self.pos_session.action_pos_session_validate()

        first_session.action_pos_session_validate()

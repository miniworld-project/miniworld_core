from miniworld.impairment import ImpairmentModel, LinkQualityConstants
from miniworld.singletons import singletons


class NetEm(ImpairmentModel.ImpairmentModel):
    NETEM_KEY_LOSS = "loss"
    NETEM_KEY_LIMIT = "limit"
    NETEM_KEY_DELAY = "delay"
    NETEM_KEY_CORRUPT = "corrupt"
    NETEM_KEY_DUPLICATE = "duplicate"
    NETEM_KEY_REORDER = "reorder"
    NETEM_KEY_RATE = "rate"

    # order of options that netem needs
    NETEM_KEYS = (
        NETEM_KEY_LIMIT, NETEM_KEY_DELAY, NETEM_KEY_LOSS, NETEM_KEY_CORRUPT, NETEM_KEY_DUPLICATE, NETEM_KEY_REORDER,
        NETEM_KEY_RATE)


class WiFiLinear(NetEm):
    MAX_BANDWIDTH = 54000

    #####################################################
    # Implement these methods in a subclass
    #####################################################

    def _distance_2_link_quality(self, distance):
        distance = distance * 1.0

        default_link_quality = \
            {self.NETEM_KEY_LOSS: None,
             self.NETEM_KEY_LIMIT: None,
             self.NETEM_KEY_DELAY: None,
             self.NETEM_KEY_CORRUPT: None,
             self.NETEM_KEY_DUPLICATE: None,
             self.NETEM_KEY_REORDER: None,
             self.NETEM_KEY_RATE: None
             }

        # distribute bandwidth linear for dist in [0, 30)
        # TODO: other way than defining maximum bandwidth?
        max_bandwidth = singletons.scenario_config.get_link_bandwidth() or self.MAX_BANDWIDTH
        distance += 1

        if distance >= 0:

            distance = distance / 2
            if distance >= 0:

                bandwidth = 1.0 * max_bandwidth / distance if distance > 1 else max_bandwidth
                default_link_quality[LinkQualityConstants.LINK_QUALITY_KEY_BANDWIDTH] = bandwidth

                delay_const = (distance - 1) * 2 if distance > 1 else 0
                delay_const_str = '%.2f' % delay_const
                delay_variation = delay_const / 10.0
                delay_variation_str = '%.2f' % delay_variation
                delay_cmd = "{delay_const}ms {delay_var}ms 25%".format(delay_const=delay_const_str,
                                                                       delay_var=delay_variation_str)
                # delay_cmd = "{delay_const} {delay_var} distribution normal".format(delay_const=delay_const, delay_var=delay_variation)
                default_link_quality[self.NETEM_KEY_DELAY] = delay_cmd
                # return bandwidth, delay_const, delay_variation

                if bandwidth >= 1000:
                    return True, default_link_quality

        return False, default_link_quality


class WiFiExponential(WiFiLinear):
    #####################################################
    # Implement these methods in a subclass
    #####################################################

    # TODO: Abstract!
    def _distance_2_link_quality(self, distance):
        """

        """

        distance = distance * 1.0

        default_link_quality = \
            {self.NETEM_KEY_LOSS: None,
             self.NETEM_KEY_LIMIT: None,
             self.NETEM_KEY_DELAY: None,
             self.NETEM_KEY_CORRUPT: None,
             self.NETEM_KEY_DUPLICATE: None,
             self.NETEM_KEY_REORDER: None,
             self.NETEM_KEY_RATE: None
             }

        # distribute bandwidth linear for dist in [0, 30)
        # TODO: other way than defining maximum bandwidth?
        max_bandwidth = singletons.scenario_config.get_link_bandwidth() or self.MAX_BANDWIDTH

        if distance >= 0:

            bandwidth_divisor = 2 ** int(distance / 4.0)

            bandwidth = 1.0 * max_bandwidth / bandwidth_divisor if distance >= 1 else max_bandwidth
            default_link_quality[LinkQualityConstants.LINK_QUALITY_KEY_BANDWIDTH] = bandwidth

            delay_const = bandwidth_divisor
            delay_const_str = '%.2f' % delay_const
            delay_variation = delay_const / 10.0
            delay_variation_str = '%.2f' % delay_variation
            delay_cmd = "{delay_const}ms {delay_var}ms 25%".format(delay_const=delay_const_str,
                                                                   delay_var=delay_variation_str)
            # delay_cmd = "{delay_const} {delay_var} distribution normal".format(delay_const=delay_const, delay_var=delay_variation)
            default_link_quality[self.NETEM_KEY_DELAY] = delay_cmd

            # return bandwidth, delay_const, delay_variation

            if bandwidth >= 1000:
                return True, default_link_quality

        return False, default_link_quality

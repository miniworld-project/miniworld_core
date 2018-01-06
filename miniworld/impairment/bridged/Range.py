from miniworld.impairment import ImpairmentModel, LinkQualityConstants

__author__ = 'Nils Schmidt'


class Range(ImpairmentModel.ImpairmentModel):
    #####################################################
    # Implement these methods in a subclass
    #####################################################

    def _distance_2_link_quality(self, distance):
        default_link_quality = {}
        if 0 <= distance < 30:
            default_link_quality.update({
                LinkQualityConstants.LINK_QUALITY_KEY_LOSS: 0
            })
            return True, default_link_quality

        return False, None
